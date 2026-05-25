"""Typed JSONL protocol payloads for CodeGopher event streams."""

from __future__ import annotations

import json
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from codegopher.core.errors import CodeGopherError

PROTOCOL_VERSION = 1
REDACTED_VALUE = "[redacted]"
SENSITIVE_CONTAINER_KEYS = {"env", "headers", "headers_env"}
SENSITIVE_KEY_PARTS = (
    "api_key",
    "apikey",
    "authorization",
    "bearer",
    "credential",
    "password",
    "passwd",
    "secret",
    "token",
)


class ProtocolPayloadError(CodeGopherError):
    """Raised when a JSONL protocol payload cannot be decoded or validated."""


class ProtocolModel(BaseModel):
    """Base shape shared by all CodeGopher JSONL protocol messages."""

    model_config = ConfigDict(extra="forbid")

    version: Literal[1] = 1
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


class TaskContractStartedEvent(ProtocolEvent):
    type: Literal["task_contract_started"] = "task_contract_started"
    turn_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    status: Literal["active", "completed", "incomplete"]
    required_tool_calls: list[str] = Field(default_factory=list)
    required_artifacts: list[str] = Field(default_factory=list)


class TaskContractUpdatedEvent(ProtocolEvent):
    type: Literal["task_contract_updated"] = "task_contract_updated"
    turn_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    status: Literal["active", "completed", "incomplete"]
    observed_tool_calls: list[str] = Field(default_factory=list)
    observed_artifacts: list[str] = Field(default_factory=list)
    recovery_attempts: int = Field(default=0, ge=0)


class TaskContractGateFailedEvent(ProtocolEvent):
    type: Literal["task_contract_gate_failed"] = "task_contract_gate_failed"
    turn_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    gate_failures: list[str] = Field(default_factory=list)
    recovery_attempts: int = Field(default=0, ge=0)


class TaskContractCompletedEvent(ProtocolEvent):
    type: Literal["task_contract_completed"] = "task_contract_completed"
    turn_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    status: Literal["completed", "incomplete"]
    outcome: str | None = None


class ConfigSnapshotEvent(ProtocolEvent):
    type: Literal["config_snapshot"] = "config_snapshot"
    workspace_root: str = Field(min_length=1)
    provider: str = Field(min_length=1)
    model: str = Field(min_length=1)
    api_family: Literal["chat_completions", "responses"]
    base_url: str | None = None
    replay_reasoning_content: bool = False
    config_sources: list[str] = Field(default_factory=list)


class McpServerSnapshotPayload(BaseModel):
    """Redacted MCP server snapshot for VS Code display."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    source: str | None = None
    server: McpServerPayload


class McpServersEvent(ProtocolEvent):
    type: Literal["mcp_servers"] = "mcp_servers"
    workspace_root: str = Field(min_length=1)
    servers: list[McpServerSnapshotPayload] = Field(default_factory=list)


class McpServerSavedEvent(ProtocolEvent):
    type: Literal["mcp_server_saved"] = "mcp_server_saved"
    workspace_root: str = Field(min_length=1)
    server_name: str = Field(min_length=1)
    server: McpServerPayload


class McpServerDeletedEvent(ProtocolEvent):
    type: Literal["mcp_server_deleted"] = "mcp_server_deleted"
    workspace_root: str = Field(min_length=1)
    server_name: str = Field(min_length=1)


_PROTOCOL_MODELS: dict[str, type[ProtocolModel]] = {
    "start_turn": StartTurnCommand,
    "approval_response": ApprovalResponseCommand,
    "cancel_turn": CancelTurnCommand,
    "shutdown": ShutdownCommand,
    "get_effective_config": GetEffectiveConfigCommand,
    "list_mcp_servers": ListMcpServersCommand,
    "save_mcp_server": SaveMcpServerCommand,
    "set_mcp_server_enabled": SetMcpServerEnabledCommand,
    "delete_mcp_server": DeleteMcpServerCommand,
    "session_started": SessionStartedEvent,
    "turn_started": TurnStartedEvent,
    "text_delta": TextDeltaEvent,
    "reasoning_delta": ReasoningDeltaEvent,
    "tool_call": ToolCallEvent,
    "approval_request": ApprovalRequestEvent,
    "tool_result": ToolResultEvent,
    "error": ErrorEvent,
    "turn_complete": TurnCompleteEvent,
    "task_contract_started": TaskContractStartedEvent,
    "task_contract_updated": TaskContractUpdatedEvent,
    "task_contract_gate_failed": TaskContractGateFailedEvent,
    "task_contract_completed": TaskContractCompletedEvent,
    "config_snapshot": ConfigSnapshotEvent,
    "mcp_servers": McpServersEvent,
    "mcp_server_saved": McpServerSavedEvent,
    "mcp_server_deleted": McpServerDeletedEvent,
}


def encode_jsonl_message(message: ProtocolModel) -> str:
    """Serialize one protocol model as a newline-terminated JSONL record."""

    return f"{message.model_dump_json()}\n"


def decode_jsonl_message(line: str) -> ProtocolModel:
    """Decode one JSONL protocol record into its typed payload model."""

    payload = line.strip()
    if not payload:
        raise ProtocolPayloadError("Empty protocol line")
    try:
        value = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise ProtocolPayloadError(f"Malformed protocol JSON: {exc.msg}") from exc
    if not isinstance(value, dict):
        raise ProtocolPayloadError("Protocol payload must be a JSON object")

    version = value.get("version")
    if version is None:
        raise ProtocolPayloadError("Protocol payload missing version")
    if version != PROTOCOL_VERSION:
        raise ProtocolPayloadError(f"Unsupported protocol version: {version}")

    message_type = value.get("type")
    if message_type is None:
        raise ProtocolPayloadError("Protocol payload missing type")
    if not isinstance(message_type, str):
        raise ProtocolPayloadError("Protocol payload type must be a string")
    model_cls = _PROTOCOL_MODELS.get(message_type)
    if model_cls is None:
        raise ProtocolPayloadError(f"Unknown protocol type: {message_type}")

    try:
        return model_cls.model_validate(value)
    except ValidationError as exc:
        raise ProtocolPayloadError(f"Invalid {message_type} payload: {exc}") from exc


def redact_protocol_value(value: Any) -> Any:
    """Return a recursively redacted copy of a protocol trace value."""

    if isinstance(value, dict):
        redacted: dict[Any, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                redacted[key] = redact_protocol_value(item)
                continue
            normalized = key.lower().replace("-", "_")
            if normalized in SENSITIVE_CONTAINER_KEYS:
                redacted[key] = _redact_container_values(item)
            elif any(part in normalized for part in SENSITIVE_KEY_PARTS):
                redacted[key] = REDACTED_VALUE
            else:
                redacted[key] = redact_protocol_value(item)
        return redacted
    if isinstance(value, list):
        return [redact_protocol_value(item) for item in value]
    return value


def _redact_container_values(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _redact_container_values(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_redact_container_values(item) for item in value]
    return REDACTED_VALUE
