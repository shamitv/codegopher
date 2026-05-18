"""Typed JSONL protocol payloads for CodeGopher event streams."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

PROTOCOL_VERSION = 1


class ProtocolModel(BaseModel):
    """Base shape shared by all CodeGopher JSONL protocol messages."""

    model_config = ConfigDict(extra="forbid")

    version: Literal[1] = PROTOCOL_VERSION
    type: str = Field(min_length=1)
    session_id: str | None = None
    turn_id: str | None = None


class ProtocolCommand(ProtocolModel):
    """Base class for commands sent to the CodeGopher event subprocess."""


class StartTurnCommand(ProtocolCommand):
    type: Literal["start_turn"] = "start_turn"
    prompt: str = Field(min_length=1)
    workspace_root: str = Field(min_length=1)
    selected_file: str | None = None
    editor_metadata: dict[str, Any] = Field(default_factory=dict)
    overrides: dict[str, Any] = Field(default_factory=dict)


class ApprovalResponseCommand(ProtocolCommand):
    type: Literal["approval_response"] = "approval_response"
    approval_id: str = Field(min_length=1)
    approved: bool
    reason: str | None = None


class CancelTurnCommand(ProtocolCommand):
    type: Literal["cancel_turn"] = "cancel_turn"
    turn_id: str = Field(min_length=1)


class ShutdownCommand(ProtocolCommand):
    type: Literal["shutdown"] = "shutdown"
