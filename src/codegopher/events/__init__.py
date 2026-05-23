"""JSONL protocol models for CodeGopher IDE integrations."""

from importlib import import_module
from typing import Any

from codegopher.events.protocol import (
    PROTOCOL_VERSION,
    ApprovalRequestEvent,
    ApprovalResponseCommand,
    CancelTurnCommand,
    ConfigSnapshotEvent,
    DeleteMcpServerCommand,
    ErrorEvent,
    GetEffectiveConfigCommand,
    ListMcpServersCommand,
    McpServerDeletedEvent,
    McpServerPayload,
    McpServerSavedEvent,
    McpServersEvent,
    McpServerSnapshotPayload,
    ProtocolCommand,
    ProtocolEvent,
    ProtocolModel,
    ProtocolPayloadError,
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
    redact_protocol_value,
)

_SESSION_EXPORTS = {
    "EventsSession",
    "EventsTurnResult",
    "agent_loop_error",
    "bad_approval_state",
    "configuration_error",
    "provider_error",
    "turn_cancelled",
}


def __getattr__(name: str) -> Any:
    if name in _SESSION_EXPORTS:
        session_module = import_module("codegopher.events.session")
        value = getattr(session_module, name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "PROTOCOL_VERSION",
    "ApprovalResponseCommand",
    "ApprovalRequestEvent",
    "CancelTurnCommand",
    "ConfigSnapshotEvent",
    "DeleteMcpServerCommand",
    "ErrorEvent",
    "GetEffectiveConfigCommand",
    "ListMcpServersCommand",
    "McpServerPayload",
    "McpServerDeletedEvent",
    "McpServerSavedEvent",
    "McpServerSnapshotPayload",
    "McpServersEvent",
    "ProtocolPayloadError",
    "ProtocolCommand",
    "ProtocolEvent",
    "ProtocolModel",
    "ReasoningDeltaEvent",
    "SaveMcpServerCommand",
    "SessionStartedEvent",
    "SetMcpServerEnabledCommand",
    "ShutdownCommand",
    "StartTurnCommand",
    "TextDeltaEvent",
    "ToolCallEvent",
    "ToolResultEvent",
    "TurnCompleteEvent",
    "TurnStartedEvent",
    "decode_jsonl_message",
    "encode_jsonl_message",
    "redact_protocol_value",
    "EventsSession",
    "EventsTurnResult",
    "agent_loop_error",
    "bad_approval_state",
    "configuration_error",
    "provider_error",
    "turn_cancelled",
]
