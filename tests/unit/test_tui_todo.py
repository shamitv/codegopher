from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from textual.widgets import Input

from codegopher.config.schema import ModelConfig, Settings, TodoConfig
from codegopher.providers.mock import MockProvider
from codegopher.tui import CodeGopherApp
from codegopher.tui.session import TuiSessionStore


def make_settings(*, todo: TodoConfig | None = None) -> Settings:
    return Settings(
        model=ModelConfig(provider="openai", name="test-model"),
        todo=todo or TodoConfig(),
    )


def make_app(
    tmp_path: Path,
    provider: MockProvider | None = None,
    *,
    settings: Settings | None = None,
) -> CodeGopherApp:
    active_provider = provider or MockProvider([[{"type": "done"}]])
    return CodeGopherApp(
        settings=settings or make_settings(),
        cwd=tmp_path,
        provider_factory=lambda _settings: active_provider,
        session_store=TuiSessionStore(data_home=tmp_path / "data"),
    )


async def submit(app: CodeGopherApp, pilot: Any, value: str) -> None:
    input_widget = app.query_one("#prompt-input", Input)
    input_widget.focus()
    input_widget.value = value
    await pilot.press("enter")
    await pilot.pause(0.1)


@pytest.mark.asyncio
async def test_todo_command_lists_empty_state_without_calling_provider(
    tmp_path: Path,
) -> None:
    provider = MockProvider([[{"type": "done"}]])
    app = make_app(tmp_path, provider)

    async with app.run_test() as pilot:
        await submit(app, pilot, "/todo")

    assert len(provider.calls) == 0
    assert app.chat_messages == ["TODO:\n- none"]
    assert app.status_message == "Displayed TODO"


@pytest.mark.asyncio
async def test_todo_command_rejects_unknown_arguments(tmp_path: Path) -> None:
    app = make_app(tmp_path)

    async with app.run_test() as pilot:
        await submit(app, pilot, "/todo nope")

    assert app.chat_messages == ["Error: Usage: /todo"]
    assert app.status_message == "Error: Usage: /todo"


@pytest.mark.asyncio
async def test_todo_add_adds_item_without_calling_provider(tmp_path: Path) -> None:
    provider = MockProvider([[{"type": "done"}]])
    app = make_app(tmp_path, provider)

    async with app.run_test() as pilot:
        await submit(app, pilot, "/todo add Review context budget tests")
        await submit(app, pilot, "/todo")

    items = app.todo_state.list()
    assert len(items) == 1
    assert items[0].text == "Review context budget tests"
    assert items[0].status == "pending"
    assert items[0].source == "user"
    assert len(provider.calls) == 0
    assert app.chat_messages == [
        f"TODO added: {items[0].id} Review context budget tests",
        "TODO:\n"
        f"- {items[0].id} [pending] Review context budget tests",
    ]
    assert app.status_message == "Displayed TODO"


@pytest.mark.asyncio
async def test_todo_add_rejects_missing_text(tmp_path: Path) -> None:
    app = make_app(tmp_path)

    async with app.run_test() as pilot:
        await submit(app, pilot, "/todo add")

    assert app.todo_state.list() == []
    assert app.chat_messages == ["Error: Usage: /todo add TEXT"]
    assert app.status_message == "Error: Usage: /todo add TEXT"


@pytest.mark.asyncio
async def test_todo_add_respects_disabled_config(tmp_path: Path) -> None:
    app = make_app(tmp_path, settings=make_settings(todo=TodoConfig(enabled=False)))

    async with app.run_test() as pilot:
        await submit(app, pilot, "/todo add Should not persist")

    assert app.todo_state.list() == []
    assert app.chat_messages == ["Error: TODO is disabled"]
    assert app.status_message == "Error: TODO is disabled"


@pytest.mark.asyncio
async def test_todo_done_marks_item_done_without_calling_provider(
    tmp_path: Path,
) -> None:
    provider = MockProvider([[{"type": "done"}]])
    app = make_app(tmp_path, provider)
    item = app.todo_state.add("Wire TODO into provider context", source="user")

    async with app.run_test() as pilot:
        await submit(app, pilot, f"/todo done {item.id}")
        await submit(app, pilot, "/todo")

    items = app.todo_state.list()
    assert items[0].status == "done"
    assert len(provider.calls) == 0
    assert app.chat_messages == [
        f"TODO done: {item.id} Wire TODO into provider context",
        "TODO:\n"
        f"- {item.id} [done] Wire TODO into provider context",
    ]
    assert app.status_message == "Displayed TODO"


@pytest.mark.asyncio
async def test_todo_done_rejects_missing_id(tmp_path: Path) -> None:
    app = make_app(tmp_path)

    async with app.run_test() as pilot:
        await submit(app, pilot, "/todo done")

    assert app.chat_messages == ["Error: Usage: /todo done ID"]
    assert app.status_message == "Error: Usage: /todo done ID"


@pytest.mark.asyncio
async def test_todo_done_rejects_unknown_id(tmp_path: Path) -> None:
    app = make_app(tmp_path)

    async with app.run_test() as pilot:
        await submit(app, pilot, "/todo done todo-missing")

    assert app.chat_messages == ["Error: TODO not found: todo-missing"]
    assert app.status_message == "Error: TODO not found: todo-missing"


@pytest.mark.asyncio
async def test_todo_state_persists_in_session_json(tmp_path: Path) -> None:
    app = make_app(tmp_path)

    async with app.run_test() as pilot:
        await submit(app, pilot, "/todo add Persist this item")

    assert app.session_store is not None
    assert app.session_state is not None
    path = app.session_store.sessions_dir / f"{app.session_state.session_id}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["todo_items"][0]["text"] == "Persist this item"
    assert data["todo_items"][0]["status"] == "pending"
    assert data["todo_items"][0]["source"] == "user"


@pytest.mark.asyncio
async def test_todo_state_resumes_from_session_json(tmp_path: Path) -> None:
    first = make_app(tmp_path)

    async with first.run_test() as pilot:
        await submit(first, pilot, "/todo add Resume this item")

    assert first.session_store is not None
    result = first.session_store.load_latest(cwd=tmp_path)
    assert result.error is None
    assert result.state is not None
    second = CodeGopherApp(
        settings=make_settings(),
        cwd=tmp_path,
        provider_factory=lambda _settings: MockProvider([[{"type": "done"}]]),
        session_store=first.session_store,
        session_state=result.state,
    )

    async with second.run_test() as pilot:
        await submit(second, pilot, "/todo")

    assert "Resume this item" in second.chat_messages[-1]


@pytest.mark.asyncio
async def test_update_todo_tool_add_renders_visible_todo_event(tmp_path: Path) -> None:
    provider = MockProvider(
        [
            [
                {
                    "type": "tool_call",
                    "tool_call": {
                        "id": "call-add",
                        "name": "update_todo",
                        "arguments": {"action": "add", "text": "Model tracked task"},
                    },
                },
                {"type": "done"},
            ],
            [{"type": "text_delta", "content": "tracked"}, {"type": "done"}],
        ]
    )
    app = make_app(tmp_path, provider)

    async with app.run_test() as pilot:
        await submit(app, pilot, "track this")

    assert any(
        message.startswith("TODO added: todo-") and "Model tracked task" in message
        for message in app.chat_messages
    )
    assert "Tool completed: update_todo" not in app.chat_messages


@pytest.mark.asyncio
async def test_update_todo_tool_done_renders_visible_todo_event(tmp_path: Path) -> None:
    provider = MockProvider(
        [
            [
                {
                    "type": "tool_call",
                    "tool_call": {
                        "id": "call-done",
                        "name": "update_todo",
                        "arguments": {"action": "done", "id": "todo-existing"},
                    },
                },
                {"type": "done"},
            ],
            [{"type": "text_delta", "content": "done"}, {"type": "done"}],
        ]
    )
    app = make_app(tmp_path, provider)
    item = app.todo_state.add("Close model task", source="user")
    app.todo_state.items[0] = item.model_copy(update={"id": "todo-existing"})

    async with app.run_test() as pilot:
        await submit(app, pilot, "finish this")

    assert "TODO done: todo-existing Close model task" in app.chat_messages
    assert "Tool completed: update_todo" not in app.chat_messages
