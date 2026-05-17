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


def make_app(tmp_path: Path, provider: MockProvider | None = None) -> CodeGopherApp:
    active_provider = provider or MockProvider([[{"type": "done"}]])
    return CodeGopherApp(
        settings=make_settings(),
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
