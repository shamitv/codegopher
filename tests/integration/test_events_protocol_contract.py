from __future__ import annotations

from codegopher.events.protocol import (
    ApprovalRequestEvent,
    ApprovalResponseCommand,
    ConfigSnapshotEvent,
    GetEffectiveConfigCommand,
    ListMcpServersCommand,
    McpServerPayload,
    McpServerSnapshotPayload,
    McpServersEvent,
    ShutdownCommand,
    StartTurnCommand,
    TextDeltaEvent,
    ToolCallEvent,
    ToolResultEvent,
    TurnCompleteEvent,
    TurnStartedEvent,
    decode_jsonl_message,
    encode_jsonl_message,
)


def test_vscode_python_protocol_contract_round_trip_stream() -> None:
    messages = [
        GetEffectiveConfigCommand(session_id="session-1", workspace_root="/repo"),
        ConfigSnapshotEvent(
            session_id="session-1",
            workspace_root="/repo",
            provider="openai",
            model="gpt-test",
            api_family="responses",
            base_url="https://api.example.test/v1",
            config_sources=["defaults", "project"],
        ),
        ListMcpServersCommand(session_id="session-1", workspace_root="/repo"),
        McpServersEvent(
            session_id="session-1",
            workspace_root="/repo",
            servers=[
                McpServerSnapshotPayload(
                    name="playwright",
                    source="project",
                    server=McpServerPayload(
                        transport="stdio",
                        command="npx",
                        args=["@playwright/mcp@latest"],
                    ),
                )
            ],
        ),
        StartTurnCommand(
            session_id="session-1",
            prompt="explain this file",
            workspace_root="/repo",
            selected_file="src/app.py",
        ),
        TurnStartedEvent(session_id="session-1", turn_id="turn-1", cwd="/repo"),
        TextDeltaEvent(session_id="session-1", turn_id="turn-1", content="I will inspect it."),
        ToolCallEvent(
            session_id="session-1",
            turn_id="turn-1",
            tool_id="tool-1",
            tool_name="read_file",
            arguments_summary='{"path":"src/app.py"}',
        ),
        ApprovalRequestEvent(
            session_id="session-1",
            turn_id="turn-1",
            approval_id="approval-1",
            tool_name="read_file",
            arguments_summary='{"path":"src/app.py"}',
            raw_arguments={"path": "src/app.py"},
        ),
        ApprovalResponseCommand(
            session_id="session-1",
            turn_id="turn-1",
            approval_id="approval-1",
            approved=True,
        ),
        ToolResultEvent(
            session_id="session-1",
            turn_id="turn-1",
            tool_id="tool-1",
            result_summary="Read 42 lines",
        ),
        TurnCompleteEvent(
            session_id="session-1",
            turn_id="turn-1",
            final_text="This file wires the app.",
            tool_count=1,
            approval_count=1,
            iteration_count=1,
        ),
        ShutdownCommand(session_id="session-1"),
    ]

    stream = "".join(encode_jsonl_message(message) for message in messages)
    decoded = [decode_jsonl_message(line) for line in stream.splitlines()]

    assert [type(message) for message in decoded] == [type(message) for message in messages]
    assert decoded == messages
