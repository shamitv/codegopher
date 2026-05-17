from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from textual.widgets import Input

from codegopher.config.schema import ModelConfig, Settings
from codegopher.providers.mock import MockProvider
from codegopher.tui import CodeGopherApp
from codegopher.tui.session import TuiSessionStore


def make_settings() -> Settings:
    return Settings(model=ModelConfig(provider="openai", name="test-model"))


def make_store(tmp_path: Path) -> TuiSessionStore:
    return TuiSessionStore(data_home=tmp_path / "data")


def make_app(
    tmp_path: Path,
    *,
    settings: Settings | None = None,
    provider: MockProvider | None = None,
) -> CodeGopherApp:
    active_provider = provider or MockProvider([[{"type": "done"}]])
    return CodeGopherApp(
        settings=settings or make_settings(),
        cwd=tmp_path,
        provider_factory=lambda _settings: active_provider,
        session_store=make_store(tmp_path),
    )


async def submit(app: CodeGopherApp, pilot: Any, value: str) -> None:
    input_widget = app.query_one("#prompt-input", Input)
    input_widget.focus()
    input_widget.value = value
    await pilot.press("enter")
    await pilot.pause(0.1)


@pytest.mark.asyncio
async def test_memory_command_lists_session_and_project_memories(tmp_path: Path) -> None:
    app = make_app(tmp_path)
    assert app.session_state is not None
    assert app.tool_context.memory_store is not None
    session_entry = app.tool_context.memory_store.add_entry(
        "session",
        session_id=app.session_state.session_id,
        content="Remember the current task",
        source="tool",
    )
    project_entry = app.tool_context.memory_store.add_entry(
        "project",
        cwd=tmp_path,
        content="Project uses pytest",
        source="user",
    )

    async with app.run_test() as pilot:
        await submit(app, pilot, "/memory")

    assert app.chat_messages == [
        "\n".join(
            [
                "Memories:",
                "Session (1):",
                f"- {session_entry.id} [session/tool] Remember the current task",
                "Project (1):",
                f"- {project_entry.id} [project/user] Project uses pytest",
            ]
        )
    ]
    assert app.status_message == "Displayed memory"


@pytest.mark.asyncio
async def test_memory_command_reports_empty_scopes(tmp_path: Path) -> None:
    app = make_app(tmp_path)

    async with app.run_test() as pilot:
        await submit(app, pilot, "/memory")

    assert app.chat_messages == ["Memories:\nSession: none\nProject: none"]
    assert app.status_message == "Displayed memory"


@pytest.mark.asyncio
async def test_memory_command_honors_disabled_memory(tmp_path: Path) -> None:
    settings = make_settings()
    settings.memory.enabled = False
    app = make_app(tmp_path, settings=settings)

    async with app.run_test() as pilot:
        await submit(app, pilot, "/memory")

    assert app.chat_messages == ["Memory is disabled"]


@pytest.mark.asyncio
async def test_memory_command_honors_disabled_scopes(tmp_path: Path) -> None:
    settings = make_settings()
    settings.memory.session_enabled = False
    settings.memory.project_enabled = False
    app = make_app(tmp_path, settings=settings)

    async with app.run_test() as pilot:
        await submit(app, pilot, "/memory")

    assert app.chat_messages == ["Memories:\nSession: disabled\nProject: disabled"]


@pytest.mark.asyncio
async def test_memory_command_rejects_arguments(tmp_path: Path) -> None:
    app = make_app(tmp_path)

    async with app.run_test() as pilot:
        await submit(app, pilot, "/memory extra")

    assert app.chat_messages == ["Error: Usage: /memory"]
    assert app.status_message == "Error: Usage: /memory"
