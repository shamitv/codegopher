from __future__ import annotations

import pytest
from pydantic import ValidationError

from codegopher.events.protocol import (
    PROTOCOL_VERSION,
    ApprovalResponseCommand,
    CancelTurnCommand,
    DeleteMcpServerCommand,
    GetEffectiveConfigCommand,
    ListMcpServersCommand,
    McpServerPayload,
    ProtocolModel,
    SaveMcpServerCommand,
    SetMcpServerEnabledCommand,
    ShutdownCommand,
    StartTurnCommand,
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
