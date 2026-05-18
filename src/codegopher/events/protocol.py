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


class ProtocolEvent(ProtocolModel):
    """Base class for events emitted by the CodeGopher event subprocess."""


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


class McpServerPayload(BaseModel):
    """Protocol representation of a configured MCP server."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    transport: Literal["stdio", "sse"] = "stdio"
    command: str | None = None
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)
    cwd: str | None = None
    startup_timeout_seconds: float = Field(default=30.0, gt=0.0)
    url: str | None = None
    headers: dict[str, str] = Field(default_factory=dict)
    headers_env: dict[str, str] = Field(default_factory=dict)
    timeout_seconds: float = Field(default=5.0, gt=0.0)
    sse_read_timeout_seconds: float = Field(default=300.0, gt=0.0)


class GetEffectiveConfigCommand(ProtocolCommand):
    type: Literal["get_effective_config"] = "get_effective_config"
    workspace_root: str = Field(min_length=1)


class ListMcpServersCommand(ProtocolCommand):
    type: Literal["list_mcp_servers"] = "list_mcp_servers"
    workspace_root: str = Field(min_length=1)


class SaveMcpServerCommand(ProtocolCommand):
    type: Literal["save_mcp_server"] = "save_mcp_server"
    workspace_root: str = Field(min_length=1)
    server_name: str = Field(min_length=1)
    server: McpServerPayload


class SetMcpServerEnabledCommand(ProtocolCommand):
    type: Literal["set_mcp_server_enabled"] = "set_mcp_server_enabled"
    workspace_root: str = Field(min_length=1)
    server_name: str = Field(min_length=1)
    enabled: bool


class DeleteMcpServerCommand(ProtocolCommand):
    type: Literal["delete_mcp_server"] = "delete_mcp_server"
    workspace_root: str = Field(min_length=1)
    server_name: str = Field(min_length=1)


class SessionStartedEvent(ProtocolEvent):
    type: Literal["session_started"] = "session_started"
    session_id: str = Field(min_length=1)
    cwd: str = Field(min_length=1)
    provider: str = Field(min_length=1)
    model: str = Field(min_length=1)
    approval_mode: Literal["review", "auto", "yolo"]


class TurnStartedEvent(ProtocolEvent):
    type: Literal["turn_started"] = "turn_started"
    session_id: str = Field(min_length=1)
    turn_id: str = Field(min_length=1)
    cwd: str = Field(min_length=1)


class TextDeltaEvent(ProtocolEvent):
    type: Literal["text_delta"] = "text_delta"
    turn_id: str = Field(min_length=1)
    content: str = Field(min_length=1)


class ReasoningDeltaEvent(ProtocolEvent):
    type: Literal["reasoning_delta"] = "reasoning_delta"
    turn_id: str = Field(min_length=1)
    content: str = Field(min_length=1)


class ToolCallEvent(ProtocolEvent):
    type: Literal["tool_call"] = "tool_call"
    turn_id: str = Field(min_length=1)
    tool_id: str = Field(min_length=1)
    tool_name: str = Field(min_length=1)
    arguments_summary: str = ""


class ApprovalRequestEvent(ProtocolEvent):
    type: Literal["approval_request"] = "approval_request"
    turn_id: str = Field(min_length=1)
    approval_id: str = Field(min_length=1)
    tool_name: str = Field(min_length=1)
    arguments_summary: str = ""
    raw_arguments: dict[str, Any] | None = None


class ToolResultEvent(ProtocolEvent):
    type: Literal["tool_result"] = "tool_result"
    turn_id: str = Field(min_length=1)
    tool_id: str = Field(min_length=1)
    is_error: bool = False
    result_summary: str = ""


class ErrorEvent(ProtocolEvent):
    type: Literal["error"] = "error"
    code: str = Field(min_length=1)
    message: str = Field(min_length=1)


class TurnCompleteEvent(ProtocolEvent):
    type: Literal["turn_complete"] = "turn_complete"
    turn_id: str = Field(min_length=1)
    final_text: str = ""
    tool_count: int = Field(default=0, ge=0)
    approval_count: int = Field(default=0, ge=0)
    iteration_count: int = Field(default=0, ge=0)
