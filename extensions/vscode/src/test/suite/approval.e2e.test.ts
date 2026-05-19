import * as assert from "node:assert/strict";
import * as fs from "node:fs/promises";
import * as os from "node:os";
import * as path from "node:path";

import { CodeGopherClient } from "../../client";
import type { ProtocolEvent } from "../../protocol";

suite("CodeGopher approval and cancellation e2e", () => {
  test("drives denial, cancellation, and recovery through a spawned events process", async function () {
    this.timeout(10000);
    const workspaceRoot = await fs.mkdtemp(path.join(os.tmpdir(), "codegopher-vscode-approval-e2e-"));
    const cliPath = await writeFakeEventsCli(workspaceRoot);
    const client = new CodeGopherClient({
      cliPath,
      workspaceRoot
    });

    try {
      const approvalRequest = waitForEvent(client, "approval_request", (event) => event.turn_id === "turn-approval");
      const approvalTurn = client.startTurn("approval-denial", { turnId: "turn-approval" });
      const approvalEvent = await approvalRequest;

      assert.equal(approvalEvent.approval_id, "approval-e2e");
      client.submitApproval(approvalEvent.approval_id, false, "Denied from VS Code.");
      assert.deepEqual(await approvalTurn, {
        version: 1,
        type: "turn_complete",
        turn_id: "turn-approval",
        final_text: "denied",
        approval_count: 1
      });

      const cancellationStarted = waitForEvent(client, "turn_started", (event) => event.turn_id === "turn-cancel");
      const cancellationTurn = client.startTurn("cancellation", { turnId: "turn-cancel" });
      await cancellationStarted;
      client.cancelTurn("turn-cancel");
      await assert.rejects(cancellationTurn, /turn_cancelled: Turn cancelled/);

      const recoveryTurn = client.startTurn("recovery", { turnId: "turn-recovery" });
      assert.deepEqual(await recoveryTurn, {
        version: 1,
        type: "turn_complete",
        turn_id: "turn-recovery",
        final_text: "recovered"
      });
    } finally {
      await client.shutdown();
      await removeTempDirectory(workspaceRoot);
    }
  });

  test("surfaces malformed stdout from a spawned events process", async function () {
    this.timeout(10000);
    const workspaceRoot = await fs.mkdtemp(path.join(os.tmpdir(), "codegopher-vscode-malformed-e2e-"));
    const cliPath = await writeFakeCli(workspaceRoot, malformedStdoutScript());
    const client = new CodeGopherClient({
      cliPath,
      workspaceRoot
    });

    try {
      await assert.rejects(client.start(), /Malformed protocol JSON/);
    } finally {
      await removeTempDirectory(workspaceRoot);
    }
  });

  test("surfaces subprocess crashes from a spawned events process", async function () {
    this.timeout(10000);
    const workspaceRoot = await fs.mkdtemp(path.join(os.tmpdir(), "codegopher-vscode-crash-e2e-"));
    const cliPath = await writeFakeCli(workspaceRoot, crashingEventsScript());
    const client = new CodeGopherClient({
      cliPath,
      workspaceRoot
    });

    try {
      const turn = client.startTurn("crash", { turnId: "turn-crash" });
      await assert.rejects(turn, /CodeGopher subprocess exited with 7: crashed/);
    } finally {
      await removeTempDirectory(workspaceRoot);
    }
  });
});

function waitForEvent<T extends ProtocolEvent["type"]>(
  client: CodeGopherClient,
  type: T,
  predicate: (event: Extract<ProtocolEvent, { type: T }>) => boolean
): Promise<Extract<ProtocolEvent, { type: T }>> {
  return new Promise((resolve) => {
    const subscription = client.onEvent((event) => {
      if (event.type !== type) {
        return;
      }
      const typedEvent = event as Extract<ProtocolEvent, { type: T }>;
      if (!predicate(typedEvent)) {
        return;
      }
      subscription.dispose();
      resolve(typedEvent);
    });
  });
}

async function writeFakeEventsCli(directory: string): Promise<string> {
  return writeFakeCli(directory, fakeEventsScript());
}

async function writeFakeCli(directory: string, script: string): Promise<string> {
  const scriptPath = path.join(directory, "fake-cgopher-events.js");
  await fs.writeFile(scriptPath, script, "utf8");
  if (process.platform === "win32") {
    const cmdPath = path.join(directory, "fake-cgopher.cmd");
    await fs.writeFile(cmdPath, `@"${process.execPath}" "${scriptPath}" %*\r\n`, "utf8");
    return cmdPath;
  }

  const cliPath = path.join(directory, "fake-cgopher");
  await fs.writeFile(
    cliPath,
    `#!/bin/sh\nexec '${shellQuote(process.execPath)}' '${shellQuote(scriptPath)}' "$@"\n`,
    "utf8"
  );
  await fs.chmod(cliPath, 0o755);
  return cliPath;
}

function shellQuote(value: string): string {
  return value.replace(/'/g, "'\\''");
}

async function removeTempDirectory(directory: string): Promise<void> {
  for (let attempt = 0; attempt < 10; attempt += 1) {
    try {
      await fs.rm(directory, { force: true, recursive: true });
      return;
    } catch (error) {
      if (!isRetryableRemoveError(error) || attempt === 9) {
        throw error;
      }
      await delay(100);
    }
  }
}

function isRetryableRemoveError(error: unknown): boolean {
  const code = (error as { code?: unknown }).code;
  return code === "EBUSY" || code === "ENOTEMPTY" || code === "EPERM";
}

function delay(milliseconds: number): Promise<void> {
  return new Promise((resolve) => {
    setTimeout(resolve, milliseconds);
  });
}

function fakeEventsScript(): string {
  return String.raw`
const readline = require("node:readline");

const rl = readline.createInterface({ input: process.stdin });
let approvalTurnId = null;

function send(message) {
  process.stdout.write(JSON.stringify(message) + "\n");
}

send({
  version: 1,
  type: "session_started",
  session_id: "session-e2e",
  cwd: process.cwd(),
  provider: "test",
  model: "test-model",
  approval_mode: "review"
});

rl.on("line", (line) => {
  const message = JSON.parse(line);
  if (message.type === "start_turn") {
    send({
      version: 1,
      type: "turn_started",
      session_id: "session-e2e",
      turn_id: message.turn_id,
      cwd: process.cwd()
    });
    if (message.prompt === "approval-denial") {
      approvalTurnId = message.turn_id;
      send({
        version: 1,
        type: "approval_request",
        turn_id: message.turn_id,
        approval_id: "approval-e2e",
        tool_name: "write_file",
        arguments_summary: "{\"path\":\"blocked.txt\"}",
        raw_arguments: { path: "blocked.txt" }
      });
      return;
    }
    if (message.prompt === "cancellation") {
      return;
    }
    send({
      version: 1,
      type: "turn_complete",
      turn_id: message.turn_id,
      final_text: "recovered"
    });
    return;
  }
  if (message.type === "approval_response") {
    send({
      version: 1,
      type: "turn_complete",
      turn_id: approvalTurnId,
      final_text: message.approved ? "approved" : "denied",
      approval_count: 1
    });
    return;
  }
  if (message.type === "cancel_turn") {
    send({
      version: 1,
      type: "error",
      turn_id: message.turn_id,
      code: "turn_cancelled",
      message: "Turn cancelled"
    });
    return;
  }
  if (message.type === "shutdown") {
    process.exit(0);
  }
});

process.on("SIGTERM", () => process.exit(0));
`;
}

function malformedStdoutScript(): string {
  return String.raw`
process.stdout.write("{not json}\n");
process.exit(0);
`;
}

function crashingEventsScript(): string {
  return String.raw`
const readline = require("node:readline");

const rl = readline.createInterface({ input: process.stdin });

function send(message) {
  process.stdout.write(JSON.stringify(message) + "\n");
}

send({
  version: 1,
  type: "session_started",
  session_id: "session-crash",
  cwd: process.cwd(),
  provider: "test",
  model: "test-model",
  approval_mode: "review"
});

rl.on("line", (line) => {
  const message = JSON.parse(line);
  if (message.type === "start_turn") {
    process.stderr.write("crashed\n");
    process.exit(7);
  }
});

process.on("SIGTERM", () => process.exit(0));
`;
}
