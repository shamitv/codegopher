from __future__ import annotations

from pathlib import Path

import pytest

from codegopher.config.schema import Settings
from codegopher.todo import TodoState
from codegopher.tools.agent_tools import UpdateTodoTool
from codegopher.tools.base import ToolContext


def make_context(tmp_path: Path, *, settings: Settings | None = None) -> ToolContext:
    return ToolContext(
        cwd=tmp_path,
        settings=settings or Settings(),
        todo_state=TodoState(max_items=(settings or Settings()).todo.max_items),
    )


@pytest.mark.asyncio
async def test_update_todo_tool_adds_session_todo(tmp_path: Path) -> None:
    context = make_context(tmp_path)

    result = await UpdateTodoTool().execute(
        {"action": "add", "text": "Keep TODO context fresh", "_tool_call_id": "call-1"},
        context,
    )

    items = context.todo_state.list() if context.todo_state else []
    assert result.is_error is False
    assert result.tool_call_id == "call-1"
    assert result.content == f"Added TODO {items[0].id}"
    assert items[0].text == "Keep TODO context fresh"
    assert items[0].status == "pending"
    assert items[0].source == "tool"


@pytest.mark.asyncio
async def test_update_todo_tool_starts_and_completes_existing_todo(
    tmp_path: Path,
) -> None:
    context = make_context(tmp_path)
    assert context.todo_state is not None
    item = context.todo_state.add("Ship the milestone", source="user")

    started = await UpdateTodoTool().execute({"action": "start", "id": item.id}, context)
    completed = await UpdateTodoTool().execute({"action": "done", "id": item.id}, context)

    assert started.is_error is False
    assert started.content == f"Updated TODO {item.id} to in_progress"
    assert completed.is_error is False
    assert completed.content == f"Updated TODO {item.id} to done"
    assert context.todo_state.list()[0].status == "done"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("arguments", "expected"),
    [
        ({"action": "add", "text": " "}, "text is required for add"),
        ({"action": "start"}, "id is required for start"),
        ({"action": "done", "id": "todo-missing"}, "TODO not found: todo-missing"),
        ({"action": "delete", "id": "todo-1"}, "action must be 'add', 'start', or 'done'"),
    ],
)
async def test_update_todo_tool_rejects_invalid_arguments(
    tmp_path: Path,
    arguments: dict[str, str],
    expected: str,
) -> None:
    context = make_context(tmp_path)

    result = await UpdateTodoTool().execute(arguments, context)

    assert result.is_error is True
    assert result.content == expected


@pytest.mark.asyncio
async def test_update_todo_tool_respects_disabled_settings(tmp_path: Path) -> None:
    context = make_context(
        tmp_path,
        settings=Settings.model_validate({"todo": {"enabled": False}}),
    )

    result = await UpdateTodoTool().execute(
        {"action": "add", "text": "Do not add"},
        context,
    )

    assert result.is_error is True
    assert result.content == "TODO is disabled in settings"
    assert context.todo_state is not None
    assert context.todo_state.list() == []


@pytest.mark.asyncio
async def test_update_todo_tool_requires_session_todo_state(tmp_path: Path) -> None:
    context = ToolContext(cwd=tmp_path)

    result = await UpdateTodoTool().execute(
        {"action": "add", "text": "Do not add"},
        context,
    )

    assert result.is_error is True
    assert result.content == "TODO state is unavailable"


@pytest.mark.asyncio
async def test_update_todo_tool_respects_item_limit(tmp_path: Path) -> None:
    settings = Settings.model_validate({"todo": {"max_items": 1}})
    context = make_context(tmp_path, settings=settings)
    assert context.todo_state is not None
    context.todo_state.add("Existing")

    result = await UpdateTodoTool().execute({"action": "add", "text": "Overflow"}, context)

    assert result.is_error is True
    assert result.content == "TODO item limit reached"


def test_update_todo_tool_does_not_require_approval() -> None:
    assert UpdateTodoTool().requires_approval is False
