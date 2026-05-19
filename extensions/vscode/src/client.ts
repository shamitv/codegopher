import { spawn } from "node:child_process";
import type { Readable, Writable } from "node:stream";

import {
  JsonlProtocolParser,
  ProtocolParseError,
  encodeProtocolMessage,
  type ApiFamily,
  type ApprovalMode,
  type ProtocolMessage,
  type SessionStartedEvent
} from "./protocol";

export interface CodeGopherClientOptions {
  cliPath: string;
  workspaceRoot: string;
  provider?: string;
  model?: string;
  baseUrl?: string;
  apiFamily?: ApiFamily | "";
  approvalMode?: ApprovalMode | "";
  spawnProcess?: SpawnProcess;
}

export interface SpawnOptions {
  cwd: string;
  stdio: ["pipe", "pipe", "pipe"];
}

export type SpawnProcess = (command: string, args: string[], options: SpawnOptions) => CodeGopherProcess;

export interface CodeGopherProcess {
  stdin: Writable;
  stdout: Readable;
  stderr: Readable;
  pid?: number;
  killed?: boolean;
  kill(signal?: string | number): boolean;
  on(event: "error", listener: (error: Error) => void): this;
  on(event: "exit", listener: (code: number | null, signal: string | null) => void): this;
  on(event: "close", listener: (code: number | null, signal: string | null) => void): this;
}

export class CodeGopherClientError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "CodeGopherClientError";
  }
}

export class SubprocessStartError extends CodeGopherClientError {
  constructor(message: string) {
    super(message);
    this.name = "SubprocessStartError";
  }
}

export class CodeGopherClient {
  private readonly options: CodeGopherClientOptions;
  private readonly spawnProcess: SpawnProcess;
  private readonly parser = new JsonlProtocolParser();
  private process: CodeGopherProcess | undefined;
  private startPromise: Promise<SessionStartedEvent> | undefined;
  private resolveStart: ((event: SessionStartedEvent) => void) | undefined;
  private rejectStart: ((error: Error) => void) | undefined;
  private session: SessionStartedEvent | undefined;

  constructor(options: CodeGopherClientOptions) {
    this.options = options;
    this.spawnProcess = options.spawnProcess ?? defaultSpawnProcess;
  }

  start(): Promise<SessionStartedEvent> {
    if (this.session) {
      return Promise.resolve(this.session);
    }
    if (this.startPromise) {
      return this.startPromise;
    }

    const args = buildCliArgs(this.options);
    this.process = this.spawnProcess(this.options.cliPath, args, {
      cwd: this.options.workspaceRoot,
      stdio: ["pipe", "pipe", "pipe"]
    });
    this.attachProcessHandlers(this.process);

    this.startPromise = new Promise<SessionStartedEvent>((resolve, reject) => {
      this.resolveStart = resolve;
      this.rejectStart = reject;
    });
    return this.startPromise;
  }

  get isRunning(): boolean {
    return this.process !== undefined && !this.process.killed;
  }

  get sessionStarted(): SessionStartedEvent | undefined {
    return this.session;
  }

  protected send(message: ProtocolMessage): void {
    if (!this.process) {
      throw new CodeGopherClientError("CodeGopher subprocess is not running.");
    }
    this.process.stdin.write(encodeProtocolMessage(message));
  }

  private attachProcessHandlers(process: CodeGopherProcess): void {
    process.stdout.on("data", (chunk: Buffer | string) => {
      this.handleStdoutChunk(chunk);
    });
    process.on("error", (error) => {
      this.rejectStartup(new SubprocessStartError(error.message));
    });
    process.on("close", (code, signal) => {
      if (!this.session) {
        this.rejectStartup(
          new SubprocessStartError(
            `CodeGopher subprocess exited before session_started (code ${formatExitCode(code, signal)}).`
          )
        );
      }
      this.process = undefined;
      this.startPromise = undefined;
    });
  }

  private handleStdoutChunk(chunk: Buffer | string): void {
    let messages: ProtocolMessage[];
    try {
      messages = this.parser.push(chunk);
    } catch (error) {
      const parseError = error instanceof Error ? error : new ProtocolParseError("Unknown protocol parse error");
      this.rejectStartup(parseError);
      return;
    }

    for (const message of messages) {
      this.handleMessage(message);
    }
  }

  private handleMessage(message: ProtocolMessage): void {
    if (message.type !== "session_started") {
      return;
    }
    this.session = message;
    this.resolveStart?.(message);
    this.resolveStart = undefined;
    this.rejectStart = undefined;
  }

  private rejectStartup(error: Error): void {
    this.rejectStart?.(error);
    this.resolveStart = undefined;
    this.rejectStart = undefined;
    this.startPromise = undefined;
  }
}

export function buildCliArgs(options: CodeGopherClientOptions): string[] {
  const args = ["--events"];
  pushOptionalArg(args, "--provider", options.provider);
  pushOptionalArg(args, "--model", options.model);
  pushOptionalArg(args, "--base-url", options.baseUrl);
  pushOptionalArg(args, "--api-family", options.apiFamily);
  pushOptionalArg(args, "--approval-mode", options.approvalMode);
  return args;
}

function pushOptionalArg(args: string[], flag: string, value: string | undefined): void {
  if (value && value.length > 0) {
    args.push(flag, value);
  }
}

function defaultSpawnProcess(command: string, args: string[], options: SpawnOptions): CodeGopherProcess {
  return spawn(command, args, options);
}

function formatExitCode(code: number | null, signal: string | null): string {
  if (code !== null) {
    return String(code);
  }
  return signal ?? "unknown";
}
