"""Shared typed payloads for providers, tools, and the agent loop."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal, NotRequired, TypeAlias, TypedDict

from pydantic import BaseModel, Field

Role: TypeAlias = Literal["system", "user", "assistant", "tool"]
MemoryScope: TypeAlias = Literal["session", "project"]
MemorySource: TypeAlias = Literal["user", "tool", "system"]
SkillSource: TypeAlias = Literal["project", "user", "builtin"]
CompactionReason: TypeAlias = Literal["manual", "automatic"]
TodoStatus: TypeAlias = Literal["pending", "in_progress", "done"]


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


class ReasoningDeltaEvent(TypedDict):
    type: Literal["reasoning_delta"]
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


StreamEvent: TypeAlias = (
    TextDeltaEvent | ReasoningDeltaEvent | ToolCallEvent | DoneEvent | ErrorEvent
)


class MemoryEntry(BaseModel):
    id: str = Field(min_length=1)
    scope: MemoryScope
    content: str = Field(min_length=1)
    source: MemorySource = "user"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    tags: list[str] = Field(default_factory=list)


class SkillMetadata(BaseModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    source: SkillSource
    description: str | None = None
    path: str | None = None
    keywords: list[str] = Field(default_factory=list)


class CompactionEntry(BaseModel):
    id: str = Field(min_length=1)
    reason: CompactionReason
    summary: str = Field(min_length=1)
    instructions: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class TodoItem(BaseModel):
    id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    status: TodoStatus = "pending"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    source: str | None = None
