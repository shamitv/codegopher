import * as assert from "node:assert/strict";
import { EventEmitter } from "node:events";
import { PassThrough } from "node:stream";

import {
  CodeGopherClient,
  CodeGopherProtocolError,
  SubprocessExitError,
  SubprocessStartError,
  buildCliArgs,
  type CodeGopherProcess,
  type SpawnOptions
} from "../../client";
import { decodeProtocolLine, encodeProtocolMessage, type ProtocolEvent, type SessionStartedEvent } from "../../protocol";

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

  test("routes typed protocol events to listeners", async () => {
    const fakeProcess = new FakeCodeGopherProcess();
    const client = new CodeGopherClient({
      cliPath: "cgopher",
      workspaceRoot: "/repo",
      spawnProcess: () => fakeProcess
    });
    const events: ProtocolEvent[] = [];
    client.onEvent((event) => {
      events.push(event);
    });

    const started = client.start();
    fakeProcess.stdout.write(allProtocolEvents.map((event) => encodeProtocolMessage(event)).join(""));

    assert.deepEqual(await started, sessionStartedEvent);
    assert.deepEqual(
      events.map((event) => event.type),
      allProtocolEvents.map((event) => event.type)
    );
  });

  test("disposes protocol event listeners", async () => {
    const fakeProcess = new FakeCodeGopherProcess();
    const client = new CodeGopherClient({
      cliPath: "cgopher",
      workspaceRoot: "/repo",
      spawnProcess: () => fakeProcess
    });
    const events: ProtocolEvent[] = [];
    const disposable = client.onEvent((event) => {
      events.push(event);
    });

    const started = client.start();
    fakeProcess.stdout.write(encodeProtocolMessage(sessionStartedEvent));
    disposable.dispose();
    fakeProcess.stdout.write(
      encodeProtocolMessage({
        version: 1,
        type: "text_delta",
        turn_id: "turn-1",
        content: "after dispose"
      })
    );

    await started;
    assert.deepEqual(events, [sessionStartedEvent]);
  });

  test("rejects startup and emits errors for invalid stdout protocol", async () => {
    const fakeProcess = new FakeCodeGopherProcess();
    const client = new CodeGopherClient({
      cliPath: "cgopher",
      workspaceRoot: "/repo",
      spawnProcess: () => fakeProcess
    });
    const errors: Error[] = [];
    client.onError((error) => {
      errors.push(error);
    });

    const started = client.start();
    fakeProcess.stdout.write("{not json}\n");

    await assert.rejects(started, /Malformed protocol JSON/);
    assert.match(errors[0].message, /Malformed protocol JSON/);
  });

  test("treats command-shaped stdout as a protocol error", async () => {
    const fakeProcess = new FakeCodeGopherProcess();
    const client = new CodeGopherClient({
      cliPath: "cgopher",
      workspaceRoot: "/repo",
      spawnProcess: () => fakeProcess
    });

    const started = client.start();
    fakeProcess.stdout.write(
      encodeProtocolMessage({
        version: 1,
        type: "shutdown"
      })
    );

    await assert.rejects(started, CodeGopherProtocolError);
  });

  test("sends start_turn and resolves matching turn_complete", async () => {
    const fakeProcess = new FakeCodeGopherProcess();
    const writes = collectStdin(fakeProcess);
    const client = startedClient(fakeProcess);

    const turn = client.startTurn("hello", {
      turnId: "turn-1",
      selectedFile: "README.md",
      editorMetadata: { language: "markdown" },
      overrides: { model: "gpt-test" }
    });
    fakeProcess.stdout.write(encodeProtocolMessage(sessionStartedEvent));
    await Promise.resolve();

    assert.deepEqual(decodeProtocolLine(writes[0]), {
      version: 1,
      type: "start_turn",
      turn_id: "turn-1",
      prompt: "hello",
      workspace_root: "/repo",
      selected_file: "README.md",
      editor_metadata: { language: "markdown" },
      overrides: { model: "gpt-test" }
    });

    fakeProcess.stdout.write(
      encodeProtocolMessage({
        version: 1,
        type: "turn_complete",
        turn_id: "turn-1",
        final_text: "done",
        tool_count: 0,
        approval_count: 0,
        iteration_count: 1
      })
    );

    assert.deepEqual(await turn, {
      version: 1,
      type: "turn_complete",
      turn_id: "turn-1",
      final_text: "done",
      tool_count: 0,
      approval_count: 0,
      iteration_count: 1
    });
  });

  test("rejects a second concurrent turn", async () => {
    const fakeProcess = new FakeCodeGopherProcess();
    const client = startedClient(fakeProcess);

    const turn = client.startTurn("first", { turnId: "turn-1" });
    fakeProcess.stdout.write(encodeProtocolMessage(sessionStartedEvent));
    await Promise.resolve();

    await assert.rejects(client.startTurn("second", { turnId: "turn-2" }), /Turn already active: turn-1/);

    fakeProcess.stdout.write(
      encodeProtocolMessage({
        version: 1,
        type: "turn_complete",
        turn_id: "turn-1"
      })
    );
    await turn;
  });

  test("rejects active turns on matching error events", async () => {
    const fakeProcess = new FakeCodeGopherProcess();
    const client = startedClient(fakeProcess);

    const turn = client.startTurn("fail", { turnId: "turn-1" });
    fakeProcess.stdout.write(encodeProtocolMessage(sessionStartedEvent));
    await Promise.resolve();
    fakeProcess.stdout.write(
      encodeProtocolMessage({
        version: 1,
        type: "error",
        turn_id: "turn-1",
        code: "provider_error",
        message: "provider failed"
      })
    );

    await assert.rejects(turn, /provider_error: provider failed/);
  });

  test("tracks approval requests and sends one approval response", async () => {
    const fakeProcess = new FakeCodeGopherProcess();
    const writes = collectStdin(fakeProcess);
    const client = startedClient(fakeProcess);

    const turn = client.startTurn("write", { turnId: "turn-1" });
    fakeProcess.stdout.write(encodeProtocolMessage(sessionStartedEvent));
    await Promise.resolve();
    fakeProcess.stdout.write(
      encodeProtocolMessage({
        version: 1,
        type: "approval_request",
        turn_id: "turn-1",
        approval_id: "approval-1",
        tool_name: "write_file",
        arguments_summary: "{\"path\":\"new.txt\"}",
        raw_arguments: { path: "new.txt" }
      })
    );

    client.submitApproval("approval-1", false, "not now");

    assert.deepEqual(decodeProtocolLine(writes[1]), {
      version: 1,
      type: "approval_response",
      approval_id: "approval-1",
      approved: false,
      reason: "not now"
    });
    assert.throws(() => client.submitApproval("approval-1", true), /No active approval request/);

    fakeProcess.stdout.write(
      encodeProtocolMessage({
        version: 1,
        type: "turn_complete",
        turn_id: "turn-1"
      })
    );
    await turn;
  });

  test("sends cancel_turn only for the active turn", async () => {
    const fakeProcess = new FakeCodeGopherProcess();
    const writes = collectStdin(fakeProcess);
    const client = startedClient(fakeProcess);

    const turn = client.startTurn("wait", { turnId: "turn-1" });
    fakeProcess.stdout.write(encodeProtocolMessage(sessionStartedEvent));
    await Promise.resolve();

    client.cancelTurn("turn-1");

    assert.deepEqual(decodeProtocolLine(writes[1]), {
      version: 1,
      type: "cancel_turn",
      turn_id: "turn-1"
    });
    assert.throws(() => client.cancelTurn("turn-2"), /No active turn for id: turn-2/);

    fakeProcess.stdout.write(
      encodeProtocolMessage({
        version: 1,
        type: "error",
        turn_id: "turn-1",
        code: "turn_cancelled",
        message: "Turn cancelled"
      })
    );
    await assert.rejects(turn, /turn_cancelled: Turn cancelled/);
  });

  test("sends effective-config command and resolves config_snapshot", async () => {
    const fakeProcess = new FakeCodeGopherProcess();
    const writes = collectStdin(fakeProcess);
    const client = startedClient(fakeProcess);

    const config = client.getEffectiveConfig();
    fakeProcess.stdout.write(encodeProtocolMessage(sessionStartedEvent));
    await Promise.resolve();

    assert.deepEqual(decodeProtocolLine(writes[0]), {
      version: 1,
      type: "get_effective_config",
      workspace_root: "/repo"
    });

    fakeProcess.stdout.write(
      encodeProtocolMessage({
        version: 1,
        type: "config_snapshot",
        workspace_root: "/repo",
        provider: "openai",
        model: "gpt-test",
        api_family: "responses",
        base_url: "https://api.example.test/v1",
        config_sources: ["defaults", "project"]
      })
    );

    assert.deepEqual(await config, {
      version: 1,
      type: "config_snapshot",
      workspace_root: "/repo",
      provider: "openai",
      model: "gpt-test",
      api_family: "responses",
      base_url: "https://api.example.test/v1",
      config_sources: ["defaults", "project"]
    });
  });

  test("sends MCP management commands and resolves matching events", async () => {
    const fakeProcess = new FakeCodeGopherProcess();
    const writes = collectStdin(fakeProcess);
    const client = startedClient(fakeProcess);
    const started = client.start();
    fakeProcess.stdout.write(encodeProtocolMessage(sessionStartedEvent));
    await started;

    const listed = client.listMcpServers();
    await Promise.resolve();
    assert.deepEqual(decodeProtocolLine(writes[0]), {
      version: 1,
      type: "list_mcp_servers",
      workspace_root: "/repo"
    });
    fakeProcess.stdout.write(
      encodeProtocolMessage({
        version: 1,
        type: "mcp_servers",
        workspace_root: "/repo",
        servers: []
      })
    );
    assert.deepEqual(await listed, {
      version: 1,
      type: "mcp_servers",
      workspace_root: "/repo",
      servers: []
    });

    const saved = client.saveMcpServer("playwright", {
      transport: "stdio",
      command: "npx",
      args: ["@playwright/mcp@latest"]
    });
    await Promise.resolve();
    assert.deepEqual(decodeProtocolLine(writes[1]), {
      version: 1,
      type: "save_mcp_server",
      workspace_root: "/repo",
      server_name: "playwright",
      server: {
        transport: "stdio",
        command: "npx",
        args: ["@playwright/mcp@latest"]
      }
    });
    fakeProcess.stdout.write(
      encodeProtocolMessage({
        version: 1,
        type: "mcp_server_saved",
        workspace_root: "/repo",
        server_name: "playwright",
        server: {
          transport: "stdio",
          command: "npx",
          args: ["@playwright/mcp@latest"]
        }
      })
    );
    assert.equal((await saved).server_name, "playwright");

    const disabled = client.setMcpServerEnabled("playwright", false);
    await Promise.resolve();
    assert.deepEqual(decodeProtocolLine(writes[2]), {
      version: 1,
      type: "set_mcp_server_enabled",
      workspace_root: "/repo",
      server_name: "playwright",
      enabled: false
    });
    fakeProcess.stdout.write(
      encodeProtocolMessage({
        version: 1,
        type: "mcp_server_saved",
        workspace_root: "/repo",
        server_name: "playwright",
        server: {
          enabled: false,
          transport: "stdio",
          command: "npx",
          args: ["@playwright/mcp@latest"]
        }
      })
    );
    assert.equal((await disabled).server.enabled, false);

    const deleted = client.deleteMcpServer("playwright");
    await Promise.resolve();
    assert.deepEqual(decodeProtocolLine(writes[3]), {
      version: 1,
      type: "delete_mcp_server",
      workspace_root: "/repo",
      server_name: "playwright"
    });
    fakeProcess.stdout.write(
      encodeProtocolMessage({
        version: 1,
        type: "mcp_server_deleted",
        workspace_root: "/repo",
        server_name: "playwright"
      })
    );
    assert.equal((await deleted).server_name, "playwright");
  });

  test("serializes management requests and rejects command-level errors", async () => {
    const fakeProcess = new FakeCodeGopherProcess();
    const client = startedClient(fakeProcess);

    const first = client.getEffectiveConfig();
    fakeProcess.stdout.write(encodeProtocolMessage(sessionStartedEvent));
    await Promise.resolve();

    await assert.rejects(client.listMcpServers(), /Management request already active: config_snapshot/);

    fakeProcess.stdout.write(
      encodeProtocolMessage({
        version: 1,
        type: "error",
        code: "configuration_error",
        message: "Invalid settings"
      })
    );

    await assert.rejects(first, /configuration_error: Invalid settings/);
  });

  test("does not start management requests while a turn is active", async () => {
    const fakeProcess = new FakeCodeGopherProcess();
    const client = startedClient(fakeProcess);

    const turn = client.startTurn("wait", { turnId: "turn-1" });
    fakeProcess.stdout.write(encodeProtocolMessage(sessionStartedEvent));
    await Promise.resolve();

    await assert.rejects(client.getEffectiveConfig(), /Turn already active: turn-1/);

    fakeProcess.stdout.write(
      encodeProtocolMessage({
        version: 1,
        type: "turn_complete",
        turn_id: "turn-1"
      })
    );
    await turn;
  });

  test("rejects active turns with structured subprocess exit errors", async () => {
    const fakeProcess = new FakeCodeGopherProcess();
    const client = startedClient(fakeProcess);
    const errors: Error[] = [];
    client.onError((error) => {
      errors.push(error);
    });

    const turn = client.startTurn("wait", { turnId: "turn-1" });
    fakeProcess.stdout.write(encodeProtocolMessage(sessionStartedEvent));
    await Promise.resolve();
    fakeProcess.stderr.write("provider exploded");
    fakeProcess.close(9, null);

    const exitError = await rejectedWith<SubprocessExitError>(turn, SubprocessExitError);
    assert.equal(exitError.command, "cgopher");
    assert.deepEqual(exitError.args, ["--events"]);
    assert.equal(exitError.cwd, "/repo");
    assert.equal(exitError.code, 9);
    assert.equal(exitError.signal, null);
    assert.equal(exitError.stderrTail, "provider exploded");
    assert.equal(errors[0], exitError);
  });

  test("rejects pending management requests on subprocess exit", async () => {
    const fakeProcess = new FakeCodeGopherProcess();
    const client = startedClient(fakeProcess);

    const config = client.getEffectiveConfig();
    fakeProcess.stdout.write(encodeProtocolMessage(sessionStartedEvent));
    await Promise.resolve();
    fakeProcess.stderr.write("invalid config");
    fakeProcess.close(2, null);

    const exitError = await rejectedWith<SubprocessExitError>(config, SubprocessExitError);
    assert.equal(exitError.stderrTail, "invalid config");
  });

  test("keeps a bounded stderr tail", async () => {
    const fakeProcess = new FakeCodeGopherProcess();
    const client = startedClient(fakeProcess);

    const turn = client.startTurn("wait", { turnId: "turn-1" });
    fakeProcess.stdout.write(encodeProtocolMessage(sessionStartedEvent));
    await Promise.resolve();
    fakeProcess.stderr.write(`prefix-${"x".repeat(9000)}`);
    fakeProcess.close(1, null);

    const exitError = await rejectedWith<SubprocessExitError>(turn, SubprocessExitError);
    assert.equal(exitError.stderrTail.length, 8000);
    assert.equal(exitError.stderrTail, "x".repeat(8000));
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

const allProtocolEvents: ProtocolEvent[] = [
  sessionStartedEvent,
  {
    version: 1,
    type: "turn_started",
    session_id: "session-1",
    turn_id: "turn-1",
    cwd: "/repo"
  },
  {
    version: 1,
    type: "text_delta",
    turn_id: "turn-1",
    content: "answer"
  },
  {
    version: 1,
    type: "reasoning_delta",
    turn_id: "turn-1",
    content: "thinking"
  },
  {
    version: 1,
    type: "tool_call",
    turn_id: "turn-1",
    tool_id: "tool-1",
    tool_name: "read_file",
    arguments_summary: "{\"path\":\"README.md\"}"
  },
  {
    version: 1,
    type: "approval_request",
    turn_id: "turn-1",
    approval_id: "approval-1",
    tool_name: "write_file",
    arguments_summary: "{\"path\":\"new.txt\"}",
    raw_arguments: { path: "new.txt" }
  },
  {
    version: 1,
    type: "tool_result",
    turn_id: "turn-1",
    tool_id: "tool-1",
    is_error: false,
    result_summary: "ok"
  },
  {
    version: 1,
    type: "error",
    code: "provider_error",
    message: "provider failed"
  },
  {
    version: 1,
    type: "turn_complete",
    turn_id: "turn-1",
    final_text: "answer",
    tool_count: 1,
    approval_count: 1,
    iteration_count: 1
  },
  {
    version: 1,
    type: "config_snapshot",
    workspace_root: "/repo",
    provider: "openai",
    model: "gpt-test",
    api_family: "responses",
    base_url: "https://api.example.test/v1",
    config_sources: ["defaults"]
  },
  {
    version: 1,
    type: "mcp_servers",
    workspace_root: "/repo",
    servers: [
      {
        name: "playwright",
        source: "project",
        server: { transport: "stdio", command: "npx", args: ["@playwright/mcp@latest"] }
      }
    ]
  },
  {
    version: 1,
    type: "mcp_server_saved",
    workspace_root: "/repo",
    server_name: "playwright",
    server: { transport: "stdio", command: "npx", args: ["@playwright/mcp@latest"] }
  },
  {
    version: 1,
    type: "mcp_server_deleted",
    workspace_root: "/repo",
    server_name: "playwright"
  }
];

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

function startedClient(fakeProcess: FakeCodeGopherProcess): CodeGopherClient {
  return new CodeGopherClient({
    cliPath: "cgopher",
    workspaceRoot: "/repo",
    spawnProcess: () => fakeProcess
  });
}

function collectStdin(fakeProcess: FakeCodeGopherProcess): string[] {
  const writes: string[] = [];
  fakeProcess.stdin.on("data", (chunk: Buffer | string) => {
    writes.push(chunk.toString());
  });
  return writes;
}

async function rejectedWith<T extends Error>(
  promise: Promise<unknown>,
  errorType: new (...args: never[]) => T
): Promise<T> {
  try {
    await promise;
  } catch (error) {
    assert.ok(error instanceof errorType);
    return error;
  }
  assert.fail(`Expected promise to reject with ${errorType.name}.`);
}
