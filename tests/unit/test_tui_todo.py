from __future__ import annotations

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
