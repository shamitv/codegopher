import * as assert from "node:assert/strict";
import { EventEmitter } from "node:events";
import * as path from "node:path";
import { PassThrough } from "node:stream";

import {
  CodeGopherClient,
  CodeGopherProtocolError,
  SubprocessExitError,
  SubprocessStartError,
  buildCliArgs,
  redactLogText,
  resolveCliPath,
  type CodeGopherProcess,
  type ProtocolTraceEntry,
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
        approvalMode: "review",
        maxIterations: 24
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
        "review",
        "--max-iterations",
        "24"
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
        approvalMode: "",
        maxIterations: undefined
      }),
      ["--events"]
    );
  });

  test("resolves CLI path settings before spawn", () => {
    const fileSystem = fakeCliPathFileSystem({
      "/repo/tools/cgopher": { mode: 0o755 },
      "/opt/cgopher": { mode: 0o755 },
      "C:\\tools\\cgopher.exe": { mode: 0o644 },
      "C:\\repo\\tools\\cgopher.exe": { mode: 0o644 }
    });

    assert.deepEqual(resolveCliPath("cgopher", "/repo", { fileSystem, pathModule: path.posix, platform: "linux" }), {
      command: "cgopher",
      source: "path"
    });
    assert.deepEqual(
      resolveCliPath("tools/cgopher", "/repo", { fileSystem, pathModule: path.posix, platform: "linux" }),
      {
        command: "/repo/tools/cgopher",
        source: "workspace"
      }
    );
    assert.deepEqual(resolveCliPath("/opt/cgopher", "/repo", { fileSystem, pathModule: path.posix, platform: "linux" }), {
      command: "/opt/cgopher",
      source: "absolute"
    });
    assert.deepEqual(
      resolveCliPath("C:\\tools\\cgopher.exe", "C:\\repo", {
        fileSystem,
        pathModule: path.win32,
        platform: "win32"
      }),
      {
        command: "C:\\tools\\cgopher.exe",
        source: "absolute"
      }
    );
    assert.deepEqual(
      resolveCliPath(".\\tools\\cgopher.exe", "C:\\repo", {
        fileSystem,
        pathModule: path.win32,
        platform: "win32"
      }),
      {
        command: "C:\\repo\\tools\\cgopher.exe",
        source: "workspace"
      }
    );
  });

  test("rejects missing and non-executable local CLI paths", () => {
    const fileSystem = fakeCliPathFileSystem({
      "/repo/not-executable": { mode: 0o644 },
      "/repo/not-file": { isFile: false, mode: 0o755 }
    });

    assert.throws(
      () => resolveCliPath("./missing", "/repo", { fileSystem, pathModule: path.posix, platform: "linux" }),
      /CodeGopher CLI not found/
    );
    assert.throws(
      () => resolveCliPath("./not-file", "/repo", { fileSystem, pathModule: path.posix, platform: "linux" }),
      /is not a file/
    );
    assert.throws(
      () => resolveCliPath("./not-executable", "/repo", { fileSystem, pathModule: path.posix, platform: "linux" }),
      /is not executable/
    );
    assert.deepEqual(
      resolveCliPath("./not-executable", "/repo", { fileSystem, pathModule: path.posix, platform: "win32" }),
      {
        command: "/repo/not-executable",
        source: "workspace"
      }
    );
  });

  test("rejects missing PATH CLI with actionable startup error", async () => {
    const client = new CodeGopherClient({
      cliPath: `codegopher-missing-cli-${process.pid}-${Date.now()}`,
      workspaceRoot: process.cwd()
    });

    await assert.rejects(client.start(), /The executable was not found.*codegopher\.cliPath/);
  });

  test("redacts secret-like lifecycle log text", () => {
    assert.equal(
      redactLogText("token=raw-token password: raw-password Authorization: Bearer raw"),
      "token=[redacted] password=[redacted] Authorization: [redacted]"
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

  test("spawns cgopher events mode with configured CLI overrides", async () => {
    const fakeProcess = new FakeCodeGopherProcess();
    const calls: Array<{ command: string; args: string[]; options: SpawnOptions }> = [];
    const client = new CodeGopherClient({
      cliPath: "cgopher",
      workspaceRoot: "/repo",
      provider: "openai",
      model: "gpt-test",
      baseUrl: "https://api.example.test/v1",
      apiFamily: "responses",
      approvalMode: "review",
      maxIterations: 24,
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
        args: [
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
          "review",
          "--max-iterations",
          "24"
        ],
        options: { cwd: "/repo", stdio: ["pipe", "pipe", "pipe"] }
      }
    ]);
    assert.deepEqual(await started, sessionStartedEvent);
  });

  test("spawns with a configured provider API key env name", async () => {
    const fakeProcess = new FakeCodeGopherProcess();
    const calls: Array<{ command: string; args: string[]; options: SpawnOptions }> = [];
    const client = new CodeGopherClient({
      cliPath: "cgopher",
      workspaceRoot: "/repo",
      apiKeyEnv: "HF_TOKEN",
      spawnProcess: (command, args, options) => {
        calls.push({ command, args, options });
        return fakeProcess;
      }
    });

    const started = client.start();
    fakeProcess.stdout.write(encodeProtocolMessage(sessionStartedEvent));

    assert.equal(calls.length, 1);
    assert.equal(calls[0]?.options.env?.CODEGOPHER_API_KEY_ENV, "HF_TOKEN");
    assert.deepEqual(await started, sessionStartedEvent);
  });

  test("injects a stored provider API key under the configured env name", async () => {
    const fakeProcess = new FakeCodeGopherProcess();
    const calls: Array<{ command: string; args: string[]; options: SpawnOptions }> = [];
    const client = new CodeGopherClient({
      cliPath: "cgopher",
      workspaceRoot: "/repo",
      apiKeyEnv: "HF_TOKEN",
      apiKeyProvider: async () => "hf-secret",
      spawnProcess: (command, args, options) => {
        calls.push({ command, args, options });
        return fakeProcess;
      }
    });

    const started = client.start();
    await waitForSpawn(calls);
    fakeProcess.stdout.write(encodeProtocolMessage(sessionStartedEvent));

    assert.equal(calls[0]?.options.env?.CODEGOPHER_API_KEY_ENV, "HF_TOKEN");
    assert.equal(calls[0]?.options.env?.HF_TOKEN, "hf-secret");
    assert.deepEqual(await started, sessionStartedEvent);
  });

  test("injects stored provider API keys as OPENAI_API_KEY by default", async () => {
    const fakeProcess = new FakeCodeGopherProcess();
    const calls: Array<{ command: string; args: string[]; options: SpawnOptions }> = [];
    const client = new CodeGopherClient({
      cliPath: "cgopher",
      workspaceRoot: "/repo",
      apiKeyProvider: () => "openai-secret",
      spawnProcess: (command, args, options) => {
        calls.push({ command, args, options });
        return fakeProcess;
      }
    });

    const started = client.start();
    await waitForSpawn(calls);
    fakeProcess.stdout.write(encodeProtocolMessage(sessionStartedEvent));

    assert.equal(calls[0]?.options.env?.CODEGOPHER_API_KEY_ENV, "OPENAI_API_KEY");
    assert.equal(calls[0]?.options.env?.OPENAI_API_KEY, "openai-secret");
    assert.deepEqual(await started, sessionStartedEvent);
  });

  test("rejects invalid API key env names before spawning", async () => {
    let spawnCount = 0;
    const client = new CodeGopherClient({
      cliPath: "cgopher",
      workspaceRoot: "/repo",
      apiKeyEnv: "bad-name",
      spawnProcess: () => {
        spawnCount += 1;
        return new FakeCodeGopherProcess();
      }
    });

    await assert.rejects(client.start(), /codegopher\.apiKeyEnv/);
    assert.equal(spawnCount, 0);
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
    assert.equal(fakeProcess.killed, true);
  });

  test("logs protocol errors through the lifecycle sink", async () => {
    const fakeProcess = new FakeCodeGopherProcess();
    const logs: string[] = [];
    const client = new CodeGopherClient({
      cliPath: "cgopher",
      workspaceRoot: "/repo",
      lifecycleSink: (message) => {
        logs.push(message);
      },
      spawnProcess: () => fakeProcess
    });

    const started = client.start();
    fakeProcess.stdout.write("{not json}\n");

    await assert.rejects(started, /Malformed protocol JSON/);
    assert.match(logs.join("\n"), /Starting CodeGopher CLI/);
    assert.match(logs.join("\n"), /CodeGopher protocol error: Malformed protocol JSON/);
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

  test("starts another turn after approval denial on the same subprocess", async () => {
    const fakeProcess = new FakeCodeGopherProcess();
    const writes = collectStdin(fakeProcess);
    const client = startedClient(fakeProcess);

    const firstTurn = client.startTurn("write", { turnId: "turn-1" });
    fakeProcess.stdout.write(encodeProtocolMessage(sessionStartedEvent));
    await Promise.resolve();
    fakeProcess.stdout.write(
      encodeProtocolMessage({
        version: 1,
        type: "approval_request",
        turn_id: "turn-1",
        approval_id: "approval-1",
        tool_name: "write_file"
      })
    );

    client.submitApproval("approval-1", false, "not now");
    fakeProcess.stdout.write(
      encodeProtocolMessage({
        version: 1,
        type: "turn_complete",
        turn_id: "turn-1",
        approval_count: 1
      })
    );
    await firstTurn;

    const secondTurn = client.startTurn("again", { turnId: "turn-2" });
    await Promise.resolve();

    assert.deepEqual(decodeProtocolLine(writes[2]), {
      version: 1,
      type: "start_turn",
      turn_id: "turn-2",
      prompt: "again",
      workspace_root: "/repo"
    });

    fakeProcess.stdout.write(
      encodeProtocolMessage({
        version: 1,
        type: "turn_complete",
        turn_id: "turn-2",
        final_text: "done"
      })
    );
    assert.deepEqual(await secondTurn, {
      version: 1,
      type: "turn_complete",
      turn_id: "turn-2",
      final_text: "done"
    });
  });

  test("starts another turn after cancellation on the same subprocess", async () => {
    const fakeProcess = new FakeCodeGopherProcess();
    const writes = collectStdin(fakeProcess);
    const client = startedClient(fakeProcess);

    const firstTurn = client.startTurn("wait", { turnId: "turn-1" });
    fakeProcess.stdout.write(encodeProtocolMessage(sessionStartedEvent));
    await Promise.resolve();

    client.cancelTurn("turn-1");
    fakeProcess.stdout.write(
      encodeProtocolMessage({
        version: 1,
        type: "error",
        turn_id: "turn-1",
        code: "turn_cancelled",
        message: "Turn cancelled"
      })
    );
    await assert.rejects(firstTurn, /turn_cancelled: Turn cancelled/);

    const secondTurn = client.startTurn("recover", { turnId: "turn-2" });
    await Promise.resolve();

    assert.deepEqual(decodeProtocolLine(writes[2]), {
      version: 1,
      type: "start_turn",
      turn_id: "turn-2",
      prompt: "recover",
      workspace_root: "/repo"
    });

    fakeProcess.stdout.write(
      encodeProtocolMessage({
        version: 1,
        type: "turn_complete",
        turn_id: "turn-2",
        final_text: "recovered"
      })
    );
    assert.deepEqual(await secondTurn, {
      version: 1,
      type: "turn_complete",
      turn_id: "turn-2",
      final_text: "recovered"
    });
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

  test("logs subprocess lifecycle events with redaction", async () => {
    const fakeProcess = new FakeCodeGopherProcess();
    const logs: string[] = [];
    const client = new CodeGopherClient({
      cliPath: "cgopher",
      workspaceRoot: "/repo",
      lifecycleSink: (message) => {
        logs.push(message);
      },
      spawnProcess: () => fakeProcess
    });

    const turn = client.startTurn("crash", { turnId: "turn-life" });
    fakeProcess.stdout.write(encodeProtocolMessage(sessionStartedEvent));
    await Promise.resolve();
    fakeProcess.stderr.write("token=raw-token\n");
    fakeProcess.close(9, null);

    await assert.rejects(turn, /CodeGopher subprocess exited with 9/);
    const joinedLogs = logs.join("\n");
    assert.match(joinedLogs, /Starting CodeGopher CLI "cgopher" in "\/repo"/);
    assert.match(joinedLogs, /CodeGopher session started: openai \/ gpt-test/);
    assert.match(joinedLogs, /CodeGopher subprocess exited/);
    assert.doesNotMatch(joinedLogs, /raw-token/);
    assert.match(joinedLogs, /\[redacted\]/);
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

  test("sends shutdown and resolves when the subprocess closes", async () => {
    const fakeProcess = new FakeCodeGopherProcess();
    const writes = collectStdin(fakeProcess);
    const errors: Error[] = [];
    const client = startedClient(fakeProcess);
    client.onError((error) => {
      errors.push(error);
    });

    const started = client.start();
    fakeProcess.stdout.write(encodeProtocolMessage(sessionStartedEvent));
    await started;

    const firstShutdown = client.shutdown();
    const secondShutdown = client.shutdown();

    assert.equal(firstShutdown, secondShutdown);
    assert.deepEqual(decodeProtocolLine(writes[0]), {
      version: 1,
      type: "shutdown"
    });

    fakeProcess.close(0, null);
    await firstShutdown;

    assert.equal(client.isRunning, false);
    assert.equal(client.sessionStarted, undefined);
    assert.deepEqual(errors, []);
  });

  test("restarts with a fresh subprocess and preserves listeners", async () => {
    const firstProcess = new FakeCodeGopherProcess();
    const secondProcess = new FakeCodeGopherProcess();
    const firstWrites = collectStdin(firstProcess);
    const events: ProtocolEvent[] = [];
    let spawnCount = 0;
    const client = new CodeGopherClient({
      cliPath: "cgopher",
      workspaceRoot: "/repo",
      spawnProcess: () => {
        spawnCount += 1;
        return spawnCount === 1 ? firstProcess : secondProcess;
      }
    });
    client.onEvent((event) => {
      events.push(event);
    });

    const started = client.start();
    firstProcess.stdout.write(encodeProtocolMessage(sessionStartedEvent));
    await started;

    const restarted = client.restart();
    await Promise.resolve();
    assert.deepEqual(decodeProtocolLine(firstWrites[0]), {
      version: 1,
      type: "shutdown"
    });
    firstProcess.close(0, null);
    await Promise.resolve();
    assert.equal(spawnCount, 2);

    const secondSession: SessionStartedEvent = {
      ...sessionStartedEvent,
      session_id: "session-2",
      model: "gpt-next"
    };
    secondProcess.stdout.write(encodeProtocolMessage(secondSession));

    assert.deepEqual(await restarted, secondSession);
    assert.deepEqual(
      events.filter((event) => event.type === "session_started"),
      [sessionStartedEvent, secondSession]
    );
  });

  test("does not trace protocol traffic when tracing is disabled", async () => {
    const fakeProcess = new FakeCodeGopherProcess();
    const traces: ProtocolTraceEntry[] = [];
    const client = new CodeGopherClient({
      cliPath: "cgopher",
      workspaceRoot: "/repo",
      traceProtocol: false,
      traceSink: (entry) => {
        traces.push(entry);
      },
      spawnProcess: () => fakeProcess
    });

    const started = client.start();
    fakeProcess.stdout.write(encodeProtocolMessage(sessionStartedEvent));
    await started;

    assert.deepEqual(traces, []);
  });

  test("traces redacted inbound and outbound protocol traffic when enabled", async () => {
    const fakeProcess = new FakeCodeGopherProcess();
    const traces: ProtocolTraceEntry[] = [];
    const client = new CodeGopherClient({
      cliPath: "cgopher",
      workspaceRoot: "/repo",
      traceProtocol: true,
      traceSink: (entry) => {
        traces.push(entry);
      },
      spawnProcess: () => fakeProcess
    });

    const saved = client.saveMcpServer("secure", {
      transport: "sse",
      url: "https://mcp.example.test/sse",
      env: { CODEGOPHER_TOKEN: "raw-env" },
      headers: { Authorization: "Bearer raw" },
      headers_env: { X_API_KEY: "RAW_ENV_NAME" }
    });
    fakeProcess.stdout.write(encodeProtocolMessage(sessionStartedEvent));
    await Promise.resolve();

    const outbound = traceMessage(traces, "out", "save_mcp_server");
    const outboundServer = traceRecord(outbound.server);
    assert.deepEqual(outboundServer.env, { CODEGOPHER_TOKEN: "[redacted]" });
    assert.deepEqual(outboundServer.headers, { Authorization: "[redacted]" });
    assert.deepEqual(outboundServer.headers_env, { X_API_KEY: "[redacted]" });

    fakeProcess.stdout.write(
      encodeProtocolMessage({
        version: 1,
        type: "mcp_server_saved",
        workspace_root: "/repo",
        server_name: "secure",
        server: {
          transport: "sse",
          url: "https://mcp.example.test/sse",
          env: { CODEGOPHER_TOKEN: "raw-env" },
          headers: { Authorization: "Bearer raw" },
          headers_env: { X_API_KEY: "RAW_ENV_NAME" }
        }
      })
    );
    await saved;

    const inbound = traceMessage(traces, "in", "mcp_server_saved");
    const inboundServer = traceRecord(inbound.server);
    assert.deepEqual(inboundServer.env, { CODEGOPHER_TOKEN: "[redacted]" });
    assert.deepEqual(inboundServer.headers, { Authorization: "[redacted]" });
    assert.deepEqual(inboundServer.headers_env, { X_API_KEY: "[redacted]" });
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

async function waitForSpawn(calls: readonly unknown[]): Promise<void> {
  for (let attempt = 0; attempt < 10 && calls.length === 0; attempt += 1) {
    await new Promise<void>((resolve) => {
      setTimeout(resolve, 0);
    });
  }
  assert.ok(calls.length > 0, "Expected CodeGopher client to spawn a subprocess.");
}

function fakeCliPathFileSystem(
  entries: Record<string, { isFile?: boolean; mode?: number }>
): {
  existsSync(candidate: string): boolean;
  statSync(candidate: string): { mode: number; isFile(): boolean };
} {
  return {
    existsSync: (candidate) => Object.hasOwn(entries, candidate),
    statSync: (candidate) => {
      const entry = entries[candidate];
      return {
        mode: entry?.mode ?? 0o755,
        isFile: () => entry?.isFile ?? true
      };
    }
  };
}

function traceMessage(
  traces: ProtocolTraceEntry[],
  direction: ProtocolTraceEntry["direction"],
  type: string
): Record<string, unknown> {
  const entry = traces.find((trace) => {
    const message = traceRecord(trace.message);
    return trace.direction === direction && message.type === type;
  });
  assert.ok(entry, `Expected ${direction} trace for ${type}.`);
  return traceRecord(entry.message);
}

function traceRecord(value: unknown): Record<string, unknown> {
  assert.equal(typeof value, "object");
  assert.notEqual(value, null);
  assert.equal(Array.isArray(value), false);
  return value as Record<string, unknown>;
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
