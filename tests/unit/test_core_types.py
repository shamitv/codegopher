from __future__ import annotations

import pytest
from pydantic import ValidationError

from codegopher.core.types import (
    CompactionEntry,
    MemoryEntry,
    Message,
    ReasoningDeltaEvent,
    SkillMetadata,
    StreamEvent,
    TodoItem,
    ToolCall,
    ToolSchema,
)


def test_core_type_imports_support_expected_shapes() -> None:
    message: Message = {"role": "user", "content": "hello"}
    tool_call: ToolCall = {"id": "call-1", "name": "read_file", "arguments": {"path": "x"}}
    schema: ToolSchema = {"type": "function", "function": {"name": "read_file"}}
    event: StreamEvent = {"type": "tool_call", "tool_call": tool_call}
    reasoning_event: ReasoningDeltaEvent = {"type": "reasoning_delta", "content": "thinking"}

    assert message["role"] == "user"
    assert schema["type"] == "function"
    assert event["type"] == "tool_call"
    assert reasoning_event["type"] == "reasoning_delta"


def test_memory_entry_model_supports_expected_shape() -> None:
    entry = MemoryEntry(
        id="mem-1",
        scope="project",
        content="Prefer pytest for focused checks.",
        source="tool",
        tags=["testing"],
    )

    assert entry.id == "mem-1"
    assert entry.scope == "project"
    assert entry.source == "tool"
    assert entry.tags == ["testing"]
    assert entry.created_at.tzinfo is not None


def test_memory_entry_rejects_invalid_scope() -> None:
    with pytest.raises(ValidationError):
        MemoryEntry(id="mem-1", scope="global", content="remember this")


def test_skill_metadata_model_supports_expected_shape() -> None:
    skill = SkillMetadata(
        id="pytest",
        name="Pytest",
        source="project",
        description="Project testing workflow",
        path=".codegopher/skills/pytest/SKILL.md",
        keywords=["tests", "pytest"],
    )

    assert skill.id == "pytest"
    assert skill.source == "project"
    assert skill.keywords == ["tests", "pytest"]


def test_skill_metadata_rejects_invalid_source() -> None:
    with pytest.raises(ValidationError):
        SkillMetadata(id="pytest", name="Pytest", source="remote")


def test_compaction_entry_model_supports_expected_shape() -> None:
    entry = CompactionEntry(
        id="compact-1",
        reason="manual",
        summary="Earlier work established the test command.",
        instructions="Keep testing details.",
    )

    assert entry.reason == "manual"
    assert entry.summary.startswith("Earlier work")
    assert entry.created_at.tzinfo is not None


def test_compaction_entry_rejects_invalid_reason() -> None:
    with pytest.raises(ValidationError):
        CompactionEntry(id="compact-1", reason="timeout", summary="summary")


def test_todo_item_model_supports_expected_shape() -> None:
    item = TodoItem(
        id="todo-1",
        text="Add schema tests",
        status="in_progress",
        source="user",
    )

    assert item.id == "todo-1"
    assert item.status == "in_progress"
    assert item.source == "user"
    assert item.updated_at.tzinfo is not None


def test_todo_item_rejects_invalid_status() -> None:
    with pytest.raises(ValidationError):
        TodoItem(id="todo-1", text="Add schema tests", status="paused")
