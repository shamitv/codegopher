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
