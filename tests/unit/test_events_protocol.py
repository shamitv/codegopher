from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from codegopher.events.protocol import (
    PROTOCOL_VERSION,
    ApprovalResponseCommand,
    ApprovalRequestEvent,
    CancelTurnCommand,
    ConfigSnapshotEvent,
    DeleteMcpServerCommand,
    ErrorEvent,
    GetEffectiveConfigCommand,
    ListMcpServersCommand,
    McpServerPayload,
    McpServerDeletedEvent,
    McpServerSavedEvent,
    McpServerSnapshotPayload,
    McpServersEvent,
    ProtocolPayloadError,
    ProtocolModel,
    ReasoningDeltaEvent,
    SaveMcpServerCommand,
    SessionStartedEvent,
    SetMcpServerEnabledCommand,
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


def test_protocol_model_defaults_common_fields() -> None:
    payload = ProtocolModel(type="test_message")

    assert payload.version == PROTOCOL_VERSION
    assert payload.type == "test_message"
    assert payload.session_id is None
    assert payload.turn_id is None


def test_protocol_model_accepts_common_ids() -> None:
    payload = ProtocolModel(
        type="test_message",
        session_id="session-1",
        turn_id="turn-1",
    )

    assert payload.session_id == "session-1"
    assert payload.turn_id == "turn-1"


def test_protocol_model_rejects_unsupported_version() -> None:
    with pytest.raises(ValidationError):
        ProtocolModel.model_validate({"version": 2, "type": "test_message"})


def test_protocol_model_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        ProtocolModel.model_validate({"type": "test_message", "extra": True})


def test_protocol_model_rejects_blank_type() -> None:
    with pytest.raises(ValidationError):
        ProtocolModel(type="")


def test_start_turn_command_supports_expected_shape() -> None:
    command = StartTurnCommand(
        session_id="session-1",
        turn_id="turn-1",
        prompt="explain this file",
        workspace_root="/repo",
        selected_file="src/app.py",
        editor_metadata={"language_id": "python"},
        overrides={"model": "gpt-test"},
    )

    assert command.type == "start_turn"
    assert command.prompt == "explain this file"
    assert command.workspace_root == "/repo"
    assert command.selected_file == "src/app.py"
    assert command.editor_metadata == {"language_id": "python"}
    assert command.overrides == {"model": "gpt-test"}


def test_start_turn_command_rejects_blank_prompt_and_workspace() -> None:
    with pytest.raises(ValidationError):
        StartTurnCommand(prompt="", workspace_root="/repo")

    with pytest.raises(ValidationError):
        StartTurnCommand(prompt="hello", workspace_root="")


def test_start_turn_command_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        StartTurnCommand(
            prompt="hello",
            workspace_root="/repo",
            unexpected=True,
        )


def test_approval_response_command_supports_approval_and_denial() -> None:
    approval = ApprovalResponseCommand(
        session_id="session-1",
        turn_id="turn-1",
        approval_id="approval-1",
        approved=True,
    )
    denial = ApprovalResponseCommand(
        approval_id="approval-2",
        approved=False,
        reason="Not this time",
    )

    assert approval.type == "approval_response"
    assert approval.approved is True
    assert approval.reason is None
    assert denial.approved is False
    assert denial.reason == "Not this time"


def test_approval_response_command_requires_approval_id() -> None:
    with pytest.raises(ValidationError):
        ApprovalResponseCommand(approval_id="", approved=True)


def test_cancel_turn_command_requires_turn_id() -> None:
    command = CancelTurnCommand(session_id="session-1", turn_id="turn-1")

    assert command.type == "cancel_turn"
    assert command.turn_id == "turn-1"

    with pytest.raises(ValidationError):
        CancelTurnCommand(turn_id="")


def test_shutdown_command_supports_session_scope() -> None:
    command = ShutdownCommand(session_id="session-1")

    assert command.type == "shutdown"
    assert command.session_id == "session-1"


def test_get_effective_config_command_requires_workspace_root() -> None:
    command = GetEffectiveConfigCommand(workspace_root="/repo")

    assert command.type == "get_effective_config"
    assert command.workspace_root == "/repo"

    with pytest.raises(ValidationError):
        GetEffectiveConfigCommand(workspace_root="")


def test_list_mcp_servers_command_requires_workspace_root() -> None:
    command = ListMcpServersCommand(workspace_root="/repo")

    assert command.type == "list_mcp_servers"
    assert command.workspace_root == "/repo"

    with pytest.raises(ValidationError):
        ListMcpServersCommand(workspace_root="")


def test_mcp_server_payload_supports_stdio_shape() -> None:
    server = McpServerPayload(
        transport="stdio",
        command="npx",
        args=["@playwright/mcp@latest"],
        env={"PLAYWRIGHT_BROWSERS_PATH": "0"},
        cwd=".",
    )

    assert server.enabled is True
    assert server.transport == "stdio"
    assert server.command == "npx"
    assert server.args == ["@playwright/mcp@latest"]
    assert server.env == {"PLAYWRIGHT_BROWSERS_PATH": "0"}
    assert server.cwd == "."


def test_mcp_server_payload_supports_sse_shape() -> None:
    server = McpServerPayload(
        transport="sse",
        url="https://example.test/sse",
        headers={"X-Test": "public"},
        headers_env={"Authorization": "MCP_AUTH"},
        timeout_seconds=10,
        sse_read_timeout_seconds=120,
    )

    assert server.transport == "sse"
    assert server.url == "https://example.test/sse"
    assert server.headers == {"X-Test": "public"}
    assert server.headers_env == {"Authorization": "MCP_AUTH"}
    assert server.timeout_seconds == 10
    assert server.sse_read_timeout_seconds == 120


def test_mcp_server_payload_rejects_invalid_transport_timeout_and_extra_fields() -> None:
    with pytest.raises(ValidationError):
        McpServerPayload(transport="http")

    with pytest.raises(ValidationError):
        McpServerPayload(startup_timeout_seconds=0)

    with pytest.raises(ValidationError):
        McpServerPayload(extra=True)


def test_save_mcp_server_command_supports_server_payload() -> None:
    command = SaveMcpServerCommand(
        workspace_root="/repo",
        server_name="playwright",
        server=McpServerPayload(command="npx"),
    )

    assert command.type == "save_mcp_server"
    assert command.workspace_root == "/repo"
    assert command.server_name == "playwright"
    assert command.server.command == "npx"


def test_save_mcp_server_command_rejects_blank_server_name() -> None:
    with pytest.raises(ValidationError):
        SaveMcpServerCommand(
            workspace_root="/repo",
            server_name="",
            server=McpServerPayload(command="npx"),
        )


def test_set_mcp_server_enabled_command_supports_boolean_state() -> None:
    command = SetMcpServerEnabledCommand(
        workspace_root="/repo",
        server_name="playwright",
        enabled=False,
    )

    assert command.type == "set_mcp_server_enabled"
    assert command.enabled is False


def test_delete_mcp_server_command_requires_server_name() -> None:
    command = DeleteMcpServerCommand(workspace_root="/repo", server_name="playwright")

    assert command.type == "delete_mcp_server"
    assert command.server_name == "playwright"

    with pytest.raises(ValidationError):
        DeleteMcpServerCommand(workspace_root="/repo", server_name="")


def test_session_started_event_supports_expected_shape() -> None:
    event = SessionStartedEvent(
        session_id="session-1",
        cwd="/repo",
        provider="openai",
        model="gpt-test",
        approval_mode="review",
    )

    assert event.type == "session_started"
    assert event.session_id == "session-1"
    assert event.cwd == "/repo"
    assert event.provider == "openai"
    assert event.model == "gpt-test"
    assert event.approval_mode == "review"


def test_session_started_event_rejects_invalid_approval_mode() -> None:
    with pytest.raises(ValidationError):
        SessionStartedEvent(
            session_id="session-1",
            cwd="/repo",
            provider="openai",
            model="gpt-test",
            approval_mode="sometimes",
        )


def test_turn_started_event_requires_turn_id_and_cwd() -> None:
    event = TurnStartedEvent(session_id="session-1", turn_id="turn-1", cwd="/repo")

    assert event.type == "turn_started"
    assert event.turn_id == "turn-1"
    assert event.cwd == "/repo"

    with pytest.raises(ValidationError):
        TurnStartedEvent(session_id="session-1", turn_id="", cwd="/repo")


def test_text_and_reasoning_delta_events_require_content() -> None:
    text = TextDeltaEvent(turn_id="turn-1", content="hello")
    reasoning = ReasoningDeltaEvent(turn_id="turn-1", content="thinking")

    assert text.type == "text_delta"
    assert text.content == "hello"
    assert reasoning.type == "reasoning_delta"
    assert reasoning.content == "thinking"

    with pytest.raises(ValidationError):
        TextDeltaEvent(turn_id="turn-1", content="")

    with pytest.raises(ValidationError):
        ReasoningDeltaEvent(turn_id="turn-1", content="")


def test_tool_call_event_supports_argument_summary() -> None:
    event = ToolCallEvent(
        turn_id="turn-1",
        tool_id="tool-1",
        tool_name="read_file",
        arguments_summary='{"path":"README.md"}',
    )

    assert event.type == "tool_call"
    assert event.tool_id == "tool-1"
    assert event.tool_name == "read_file"
    assert "README.md" in event.arguments_summary


def test_approval_request_event_supports_optional_raw_arguments() -> None:
    event = ApprovalRequestEvent(
        turn_id="turn-1",
        approval_id="approval-1",
        tool_name="write_file",
        arguments_summary='{"path":"README.md"}',
        raw_arguments={"path": "README.md", "content": "new"},
    )

    assert event.type == "approval_request"
    assert event.approval_id == "approval-1"
    assert event.raw_arguments == {"path": "README.md", "content": "new"}


def test_tool_result_event_supports_error_state() -> None:
    event = ToolResultEvent(
        turn_id="turn-1",
        tool_id="tool-1",
        is_error=True,
        result_summary="Denied by user",
    )

    assert event.type == "tool_result"
    assert event.is_error is True
    assert event.result_summary == "Denied by user"


def test_error_event_requires_code_and_message() -> None:
    event = ErrorEvent(code="provider_error", message="provider failed")

    assert event.type == "error"
    assert event.code == "provider_error"
    assert event.message == "provider failed"

    with pytest.raises(ValidationError):
        ErrorEvent(code="", message="provider failed")

    with pytest.raises(ValidationError):
        ErrorEvent(code="provider_error", message="")


def test_turn_complete_event_supports_counts() -> None:
    event = TurnCompleteEvent(
        turn_id="turn-1",
        final_text="done",
        tool_count=2,
        approval_count=1,
        iteration_count=3,
    )

    assert event.type == "turn_complete"
    assert event.final_text == "done"
    assert event.tool_count == 2
    assert event.approval_count == 1
    assert event.iteration_count == 3


def test_turn_complete_event_rejects_negative_counts() -> None:
    with pytest.raises(ValidationError):
        TurnCompleteEvent(turn_id="turn-1", tool_count=-1)


def test_config_snapshot_event_supports_endpoint_metadata() -> None:
    event = ConfigSnapshotEvent(
        workspace_root="/repo",
        provider="openai",
        model="gpt-test",
        api_family="responses",
        base_url="https://api.example.test/v1",
        config_sources=["defaults", "project"],
    )

    assert event.type == "config_snapshot"
    assert event.provider == "openai"
    assert event.model == "gpt-test"
    assert event.api_family == "responses"
    assert event.base_url == "https://api.example.test/v1"
    assert event.config_sources == ["defaults", "project"]


def test_config_snapshot_event_rejects_invalid_api_family() -> None:
    with pytest.raises(ValidationError):
        ConfigSnapshotEvent(
            workspace_root="/repo",
            provider="openai",
            model="gpt-test",
            api_family="assistants",
        )


def test_mcp_server_snapshot_payload_supports_source_metadata() -> None:
    snapshot = McpServerSnapshotPayload(
        name="playwright",
        source="project",
        server=McpServerPayload(command="npx"),
    )

    assert snapshot.name == "playwright"
    assert snapshot.source == "project"
    assert snapshot.server.command == "npx"


def test_mcp_server_snapshot_payload_rejects_blank_name() -> None:
    with pytest.raises(ValidationError):
        McpServerSnapshotPayload(name="", server=McpServerPayload(command="npx"))


def test_mcp_servers_event_supports_empty_and_populated_lists() -> None:
    empty = McpServersEvent(workspace_root="/repo")
    populated = McpServersEvent(
        workspace_root="/repo",
        servers=[
            McpServerSnapshotPayload(
                name="playwright",
                source="project",
                server=McpServerPayload(command="npx"),
            )
        ],
    )

    assert empty.type == "mcp_servers"
    assert empty.servers == []
    assert populated.servers[0].name == "playwright"


def test_mcp_server_saved_event_supports_normalized_payload() -> None:
    event = McpServerSavedEvent(
        workspace_root="/repo",
        server_name="playwright",
        server=McpServerPayload(command="npx"),
    )

    assert event.type == "mcp_server_saved"
    assert event.server_name == "playwright"
    assert event.server.command == "npx"


def test_mcp_server_deleted_event_requires_server_name() -> None:
    event = McpServerDeletedEvent(workspace_root="/repo", server_name="playwright")

    assert event.type == "mcp_server_deleted"
    assert event.server_name == "playwright"

    with pytest.raises(ValidationError):
        McpServerDeletedEvent(workspace_root="/repo", server_name="")


def all_protocol_messages() -> list[ProtocolModel]:
    return [
        StartTurnCommand(prompt="hello", workspace_root="/repo"),
        ApprovalResponseCommand(approval_id="approval-1", approved=True),
        CancelTurnCommand(turn_id="turn-1"),
        ShutdownCommand(),
        GetEffectiveConfigCommand(workspace_root="/repo"),
        ListMcpServersCommand(workspace_root="/repo"),
        SaveMcpServerCommand(
            workspace_root="/repo",
            server_name="playwright",
            server=McpServerPayload(command="npx"),
        ),
        SetMcpServerEnabledCommand(
            workspace_root="/repo",
            server_name="playwright",
            enabled=True,
        ),
        DeleteMcpServerCommand(workspace_root="/repo", server_name="playwright"),
        SessionStartedEvent(
            session_id="session-1",
            cwd="/repo",
            provider="openai",
            model="gpt-test",
            approval_mode="review",
        ),
        TurnStartedEvent(session_id="session-1", turn_id="turn-1", cwd="/repo"),
        TextDeltaEvent(turn_id="turn-1", content="hello"),
        ReasoningDeltaEvent(turn_id="turn-1", content="thinking"),
        ToolCallEvent(turn_id="turn-1", tool_id="tool-1", tool_name="read_file"),
        ApprovalRequestEvent(
            turn_id="turn-1",
            approval_id="approval-1",
            tool_name="read_file",
        ),
        ToolResultEvent(turn_id="turn-1", tool_id="tool-1", result_summary="ok"),
        ErrorEvent(code="provider_error", message="provider failed"),
        TurnCompleteEvent(turn_id="turn-1", final_text="done"),
        ConfigSnapshotEvent(
            workspace_root="/repo",
            provider="openai",
            model="gpt-test",
            api_family="chat_completions",
        ),
        McpServersEvent(workspace_root="/repo"),
        McpServerSavedEvent(
            workspace_root="/repo",
            server_name="playwright",
            server=McpServerPayload(command="npx"),
        ),
        McpServerDeletedEvent(workspace_root="/repo", server_name="playwright"),
    ]


@pytest.mark.parametrize("message", all_protocol_messages())
def test_jsonl_round_trips_all_protocol_messages(message: ProtocolModel) -> None:
    encoded = encode_jsonl_message(message)
    decoded = decode_jsonl_message(encoded)

    assert encoded.endswith("\n")
    assert encoded.count("\n") == 1
    assert type(decoded) is type(message)
    assert decoded == message


def test_encode_jsonl_message_returns_json_object_line() -> None:
    encoded = encode_jsonl_message(ShutdownCommand(session_id="session-1"))
    loaded = json.loads(encoded)

    assert loaded["version"] == PROTOCOL_VERSION
    assert loaded["type"] == "shutdown"
    assert loaded["session_id"] == "session-1"


def test_decode_jsonl_message_rejects_empty_line() -> None:
    with pytest.raises(ProtocolPayloadError, match="Empty protocol line"):
        decode_jsonl_message("\n")


def test_decode_jsonl_message_rejects_malformed_json() -> None:
    with pytest.raises(ProtocolPayloadError, match="Malformed protocol JSON"):
        decode_jsonl_message("{")


def test_decode_jsonl_message_rejects_non_object_json() -> None:
    with pytest.raises(ProtocolPayloadError, match="must be a JSON object"):
        decode_jsonl_message("[]")


def test_decode_jsonl_message_requires_version() -> None:
    with pytest.raises(ProtocolPayloadError, match="missing version"):
        decode_jsonl_message('{"type":"shutdown"}')


def test_decode_jsonl_message_rejects_unsupported_version() -> None:
    with pytest.raises(ProtocolPayloadError, match="Unsupported protocol version"):
        decode_jsonl_message('{"version":2,"type":"shutdown"}')


def test_decode_jsonl_message_requires_type() -> None:
    with pytest.raises(ProtocolPayloadError, match="missing type"):
        decode_jsonl_message('{"version":1}')


def test_decode_jsonl_message_rejects_non_string_type() -> None:
    with pytest.raises(ProtocolPayloadError, match="type must be a string"):
        decode_jsonl_message('{"version":1,"type":123}')


def test_decode_jsonl_message_rejects_unknown_type() -> None:
    with pytest.raises(ProtocolPayloadError, match="Unknown protocol type"):
        decode_jsonl_message('{"version":1,"type":"mystery"}')


def test_decode_jsonl_message_rejects_extra_fields() -> None:
    with pytest.raises(ProtocolPayloadError, match="Invalid shutdown payload"):
        decode_jsonl_message('{"version":1,"type":"shutdown","unexpected":true}')


def test_decode_jsonl_message_rejects_validation_failures() -> None:
    with pytest.raises(ProtocolPayloadError, match="Invalid start_turn payload"):
        decode_jsonl_message('{"version":1,"type":"start_turn","prompt":"","workspace_root":"/repo"}')
