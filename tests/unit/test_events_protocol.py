from __future__ import annotations

import pytest
from pydantic import ValidationError

from codegopher.events.protocol import (
    PROTOCOL_VERSION,
    ApprovalResponseCommand,
    CancelTurnCommand,
    ProtocolModel,
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
