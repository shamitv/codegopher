import { spawn } from "node:child_process";
import { randomUUID } from "node:crypto";
import type { Readable, Writable } from "node:stream";

import {
  JsonlProtocolParser,
  ProtocolParseError,
  encodeProtocolMessage,
  isProtocolEvent,
  type ApiFamily,
  type ApprovalMode,
  type ApprovalRequestEvent,
  type ErrorEvent,
  type ProtocolEvent,
  type ProtocolMessage,
  type SessionStartedEvent,
  type StartTurnCommand,
  type TurnCompleteEvent
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

export class CodeGopherProtocolError extends CodeGopherClientError {
  constructor(message: string) {
    super(message);
    this.name = "CodeGopherProtocolError";
  }
}

export interface Disposable {
  dispose(): void;
}

export type ProtocolEventListener = (event: ProtocolEvent) => void;
export type ClientErrorListener = (error: CodeGopherClientError | ProtocolParseError) => void;

export interface StartTurnOptions {
  turnId?: string;
  selectedFile?: string | null;
  editorMetadata?: Record<string, unknown>;
  overrides?: Record<string, unknown>;
}

interface PendingTurn {
  turnId: string;
  resolve: (event: TurnCompleteEvent) => void;
  reject: (error: Error) => void;
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
  private readonly eventListeners = new Set<ProtocolEventListener>();
  private readonly errorListeners = new Set<ClientErrorListener>();
  private activeTurn: PendingTurn | undefined;
  private readonly activeApprovals = new Map<string, ApprovalRequestEvent>();

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

  onEvent(listener: ProtocolEventListener): Disposable {
    this.eventListeners.add(listener);
    return {
      dispose: () => {
        this.eventListeners.delete(listener);
      }
    };
  }

  onError(listener: ClientErrorListener): Disposable {
    this.errorListeners.add(listener);
    return {
      dispose: () => {
        this.errorListeners.delete(listener);
      }
    };
  }

  async startTurn(prompt: string, options: StartTurnOptions = {}): Promise<TurnCompleteEvent> {
    if (this.activeTurn) {
      throw new CodeGopherClientError(`Turn already active: ${this.activeTurn.turnId}`);
    }

    const turnId = options.turnId ?? `turn-${randomUUID()}`;
    const command: StartTurnCommand = {
      version: 1,
      type: "start_turn",
      turn_id: turnId,
      prompt,
      workspace_root: this.options.workspaceRoot
    };
    if (options.selectedFile !== undefined) {
      command.selected_file = options.selectedFile;
    }
    if (options.editorMetadata !== undefined) {
      command.editor_metadata = options.editorMetadata;
    }
    if (options.overrides !== undefined) {
      command.overrides = options.overrides;
    }

    let resolveTurn: (event: TurnCompleteEvent) => void = () => undefined;
    let rejectTurn: (error: Error) => void = () => undefined;
    const turnPromise = new Promise<TurnCompleteEvent>((resolve, reject) => {
      resolveTurn = resolve;
      rejectTurn = reject;
    });
    const pendingTurn: PendingTurn = { turnId, resolve: resolveTurn, reject: rejectTurn };
    this.activeTurn = pendingTurn;

    try {
      await this.start();
      this.send(command);
    } catch (error) {
      if (this.activeTurn === pendingTurn) {
        pendingTurn.reject(error instanceof Error ? error : new CodeGopherClientError("Failed to send start_turn."));
        this.activeTurn = undefined;
      }
    }

    return turnPromise;
  }

  submitApproval(approvalId: string, approved: boolean, reason?: string | null): void {
    if (!this.activeApprovals.has(approvalId)) {
      throw new CodeGopherClientError(`No active approval request for id: ${approvalId}`);
    }
    this.activeApprovals.delete(approvalId);
    this.send({
      version: 1,
      type: "approval_response",
      approval_id: approvalId,
      approved,
      reason
    });
  }

  cancelTurn(turnId: string): void {
    if (!this.activeTurn || this.activeTurn.turnId !== turnId) {
      throw new CodeGopherClientError(`No active turn for id: ${turnId}`);
    }
    this.send({
      version: 1,
      type: "cancel_turn",
      turn_id: turnId
    });
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
      if (error instanceof ProtocolParseError) {
        this.handleClientError(error);
      } else if (error instanceof Error) {
        this.handleClientError(new CodeGopherProtocolError(error.message));
      } else {
        this.handleClientError(new ProtocolParseError("Unknown protocol parse error"));
      }
      return;
    }

    for (const message of messages) {
      this.handleMessage(message);
    }
  }

  private handleMessage(message: ProtocolMessage): void {
    if (!isProtocolEvent(message)) {
      this.handleClientError(new CodeGopherProtocolError(`Unexpected protocol command on stdout: ${message.type}`));
      return;
    }
    this.emitEvent(message);
    this.handleProtocolEvent(message);
  }

  private handleProtocolEvent(event: ProtocolEvent): void {
    if (event.type === "approval_request") {
      this.activeApprovals.set(event.approval_id, event);
      return;
    }
    if (event.type === "turn_complete") {
      this.resolveTurn(event);
      return;
    }
    if (event.type === "error") {
      this.rejectTurnIfMatched(event);
      return;
    }
    if (event.type !== "session_started") {
      return;
    }
    this.session = event;
    this.resolveStart?.(event);
    this.resolveStart = undefined;
    this.rejectStart = undefined;
  }

  private resolveTurn(event: TurnCompleteEvent): void {
    if (!this.activeTurn || this.activeTurn.turnId !== event.turn_id) {
      return;
    }
    const turn = this.activeTurn;
    this.activeTurn = undefined;
    this.activeApprovals.clear();
    turn.resolve(event);
  }

  private rejectTurnIfMatched(event: ErrorEvent): void {
    if (!this.activeTurn || event.turn_id !== this.activeTurn.turnId) {
      return;
    }
    const turn = this.activeTurn;
    this.activeTurn = undefined;
    this.activeApprovals.clear();
    turn.reject(new CodeGopherClientError(`${event.code}: ${event.message}`));
  }

  private failPendingOperations(error: Error): void {
    if (this.activeTurn) {
      this.activeTurn.reject(error);
      this.activeTurn = undefined;
    }
    this.activeApprovals.clear();
  }

  private rejectStartup(error: Error): void {
    this.rejectStart?.(error);
    this.resolveStart = undefined;
    this.rejectStart = undefined;
    this.startPromise = undefined;
  }

  private handleClientError(error: CodeGopherClientError | ProtocolParseError): void {
    this.failPendingOperations(error);
    this.rejectStartup(error);
    for (const listener of [...this.errorListeners]) {
      listener(error);
    }
  }

  private emitEvent(event: ProtocolEvent): void {
    for (const listener of [...this.eventListeners]) {
      listener(event);
    }
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
