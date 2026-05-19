import * as assert from "node:assert/strict";
import { EventEmitter } from "node:events";
import { PassThrough } from "node:stream";

import {
  CodeGopherClient,
  SubprocessStartError,
  buildCliArgs,
  type CodeGopherProcess,
  type SpawnOptions
} from "../../client";
import { encodeProtocolMessage, type SessionStartedEvent } from "../../protocol";

suite("CodeGopherClient startup", () => {
  test("builds cli args with non-empty overrides", () => {
    assert.deepEqual(
      buildCliArgs({
        cliPath: "cgopher",
        workspaceRoot: "/repo",
        provider: "openai",
        model: "gpt-test",
        baseUrl: "https://api.example.test/v1",
        apiFamily: "responses",
        approvalMode: "review"
      }),
      [
        "--events",
        "--provider",
        "openai",
        "--model",
        "gpt-test",
        "--base-url",
        "https://api.example.test/v1",
        "--api-family",
        "responses",
        "--approval-mode",
        "review"
      ]
    );
  });

  test("omits empty cli overrides", () => {
    assert.deepEqual(
      buildCliArgs({
        cliPath: "cgopher",
        workspaceRoot: "/repo",
        provider: "",
        model: undefined,
        baseUrl: "",
        apiFamily: "",
        approvalMode: ""
      }),
      ["--events"]
    );
  });

  test("spawns cgopher events mode in the workspace root", async () => {
    const fakeProcess = new FakeCodeGopherProcess();
    const calls: Array<{ command: string; args: string[]; options: SpawnOptions }> = [];
    const client = new CodeGopherClient({
      cliPath: "cgopher",
      workspaceRoot: "/repo",
      model: "gpt-test",
      spawnProcess: (command, args, options) => {
        calls.push({ command, args, options });
        return fakeProcess;
      }
    });

    const started = client.start();
    fakeProcess.stdout.write(encodeProtocolMessage(sessionStartedEvent));

    assert.deepEqual(calls, [
      {
        command: "cgopher",
        args: ["--events", "--model", "gpt-test"],
        options: { cwd: "/repo", stdio: ["pipe", "pipe", "pipe"] }
      }
    ]);
    assert.deepEqual(await started, sessionStartedEvent);
    assert.deepEqual(client.sessionStarted, sessionStartedEvent);
    assert.equal(client.isRunning, true);
  });

  test("returns the existing startup promise when called twice", async () => {
    const fakeProcess = new FakeCodeGopherProcess();
    let spawnCount = 0;
    const client = new CodeGopherClient({
      cliPath: "cgopher",
      workspaceRoot: "/repo",
      spawnProcess: () => {
        spawnCount += 1;
        return fakeProcess;
      }
    });

    const first = client.start();
    const second = client.start();
    fakeProcess.stdout.write(encodeProtocolMessage(sessionStartedEvent));

    assert.equal(first, second);
    assert.deepEqual(await first, sessionStartedEvent);
    assert.equal(spawnCount, 1);
  });

  test("rejects startup when the subprocess exits before session_started", async () => {
    const fakeProcess = new FakeCodeGopherProcess();
    const client = new CodeGopherClient({
      cliPath: "cgopher",
      workspaceRoot: "/repo",
      spawnProcess: () => fakeProcess
    });

    const started = client.start();
    fakeProcess.close(7, null);

    await assert.rejects(started, SubprocessStartError);
  });
});

const sessionStartedEvent: SessionStartedEvent = {
  version: 1,
  type: "session_started",
  session_id: "session-1",
  cwd: "/repo",
  provider: "openai",
  model: "gpt-test",
  approval_mode: "review"
};

class FakeCodeGopherProcess extends EventEmitter implements CodeGopherProcess {
  readonly stdin = new PassThrough();
  readonly stdout = new PassThrough();
  readonly stderr = new PassThrough();
  killed = false;

  kill(signal?: string | number): boolean {
    this.killed = true;
    const normalizedSignal = typeof signal === "string" ? signal : null;
    this.close(null, normalizedSignal);
    return true;
  }

  close(code: number | null, signal: string | null): void {
    this.emit("exit", code, signal);
    this.emit("close", code, signal);
  }
}
