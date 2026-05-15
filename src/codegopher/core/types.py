"""Shared typed payloads for providers, tools, and the agent loop."""

from __future__ import annotations

from typing import Any, Literal, NotRequired, TypeAlias, TypedDict


Role: TypeAlias = Literal["system", "user", "assistant", "tool"]


class Message(TypedDict, total=False):
    role: Role
    content: str | None
    name: str
    tool_call_id: str
    tool_calls: list[dict[str, Any]]


class ToolCall(TypedDict):
    id: str
    name: str
    arguments: dict[str, Any]


class ToolSchema(TypedDict):
    type: Literal["function"]
    function: dict[str, Any]


class TextDeltaEvent(TypedDict):
    type: Literal["text_delta"]
    content: str


class ToolCallEvent(TypedDict):
    type: Literal["tool_call"]
    tool_call: ToolCall


class DoneEvent(TypedDict):
    type: Literal["done"]
    finish_reason: NotRequired[str | None]


class ErrorEvent(TypedDict):
    type: Literal["error"]
    message: str


StreamEvent: TypeAlias = TextDeltaEvent | ToolCallEvent | DoneEvent | ErrorEvent

