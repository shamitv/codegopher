import * as assert from "node:assert/strict";

import {
  JsonlProtocolParser,
  ProtocolParseError,
  decodeProtocolLine,
  encodeProtocolMessage,
  type ApprovalResponseCommand,
  type ConfigSnapshotEvent,
  type GetEffectiveConfigCommand,
  type McpServersEvent,
  type SessionStartedEvent,
  type StartTurnCommand,
  type TextDeltaEvent,
  type ToolCallEvent,
  type TurnCompleteEvent
} from "../../protocol";

suite("protocol JSONL", () => {
  test("encodes and decodes typed protocol messages", () => {
    const command: StartTurnCommand = {
      version: 1,
      type: "start_turn",
      turn_id: "turn-1",
      prompt: "explain this",
      workspace_root: "/repo",
      selected_file: "src/app.ts",
      editor_metadata: { language: "typescript" },
      overrides: { model: "gpt-test" }
    };

    const decoded = decodeProtocolLine(encodeProtocolMessage(command));

    assert.deepEqual(decoded, command);
  });

  test("decodes representative events", () => {
    const messages = [
      {
        version: 1,
        type: "session_started",
        session_id: "session-1",
        cwd: "/repo",
        provider: "openai",
        model: "gpt-test",
        approval_mode: "review"
      } satisfies SessionStartedEvent,
      {
        version: 1,
        type: "text_delta",
        turn_id: "turn-1",
        content: "hello"
      } satisfies TextDeltaEvent,
      {
        version: 1,
        type: "tool_call",
        turn_id: "turn-1",
        tool_id: "tool-1",
        tool_name: "read_file",
        arguments_summary: "{\"path\":\"README.md\"}"
      } satisfies ToolCallEvent,
      {
        version: 1,
        type: "turn_complete",
        turn_id: "turn-1",
        final_text: "done",
        tool_count: 1,
        approval_count: 0,
        iteration_count: 1
      } satisfies TurnCompleteEvent,
      {
        version: 1,
        type: "config_snapshot",
        workspace_root: "/repo",
        provider: "openai",
        model: "gpt-test",
        api_family: "responses",
        base_url: "https://api.example.test/v1",
        config_sources: ["defaults", "project"]
      } satisfies ConfigSnapshotEvent,
      {
        version: 1,
        type: "mcp_servers",
        workspace_root: "/repo",
        servers: [
          {
            name: "playwright",
            source: "project",
            server: {
              transport: "stdio",
              command: "npx",
              args: ["@playwright/mcp@latest"]
            }
          }
        ]
      } satisfies McpServersEvent
    ];

    assert.deepEqual(
      messages.map((message) => decodeProtocolLine(JSON.stringify(message))),
      messages
    );
  });

  test("rejects malformed lines and invalid protocol metadata", () => {
    assert.throws(() => decodeProtocolLine(""), /Empty protocol line/);
    assert.throws(() => decodeProtocolLine("{not json}"), /Malformed protocol JSON/);
    assert.throws(() => decodeProtocolLine("[]"), /Protocol payload must be a JSON object/);
    assert.throws(() => decodeProtocolLine(JSON.stringify({ type: "shutdown" })), /missing version/);
    assert.throws(
      () => decodeProtocolLine(JSON.stringify({ version: 2, type: "shutdown" })),
      /Unsupported protocol version/
    );
    assert.throws(
      () => decodeProtocolLine(JSON.stringify({ version: 1, type: "new_thing" })),
      /Unknown protocol type/
    );
  });

  test("rejects missing required fields", () => {
    assert.throws(
      () => decodeProtocolLine(JSON.stringify({ version: 1, type: "start_turn", workspace_root: "/repo" })),
      /prompt must be a non-empty string/
    );
    assert.throws(
      () =>
        decodeProtocolLine(
          JSON.stringify({ version: 1, type: "approval_response", approval_id: "approval-1" })
        ),
      /approved must be a boolean/
    );
  });

  test("buffers partial JSONL chunks", () => {
    const parser = new JsonlProtocolParser();
    const configCommand: GetEffectiveConfigCommand = {
      version: 1,
      type: "get_effective_config",
      workspace_root: "/repo"
    };
    const approvalCommand: ApprovalResponseCommand = {
      version: 1,
      type: "approval_response",
      approval_id: "approval-1",
      approved: true
    };
    const stream = encodeProtocolMessage(configCommand) + encodeProtocolMessage(approvalCommand);

    assert.deepEqual(parser.push(stream.slice(0, 10)), []);
    assert.deepEqual(parser.push(Buffer.from(stream.slice(10, 38))), []);
    assert.deepEqual(parser.push(stream.slice(38)), [configCommand, approvalCommand]);
  });

  test("handles CRLF and flushes a final unterminated line", () => {
    const parser = new JsonlProtocolParser();
    const message = {
      version: 1,
      type: "text_delta",
      turn_id: "turn-1",
      content: "hello"
    } satisfies TextDeltaEvent;

    assert.deepEqual(parser.push(`${JSON.stringify(message)}\r\n`), [message]);
    assert.deepEqual(parser.push(JSON.stringify(message)), []);
    assert.deepEqual(parser.flush(), [message]);
  });

  test("uses a structured parse error type", () => {
    assert.throws(() => decodeProtocolLine("{"), ProtocolParseError);
  });
});
