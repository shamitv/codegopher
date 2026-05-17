from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from textual.widgets import Input

from codegopher.config.schema import ApprovalMode, ModelConfig, Settings
from codegopher.providers.mock import MockProvider
from codegopher.tui import CodeGopherApp
from codegopher.tui.session import TuiSessionState, TuiSessionStore


def make_settings() -> Settings:
    return Settings(
        model=ModelConfig(provider="openai", name="test-model"),
        approval_mode=ApprovalMode.yolo,
    )


def make_store(tmp_path: Path) -> TuiSessionStore:
    return TuiSessionStore(data_home=tmp_path / "data")


async def submit(app: CodeGopherApp, pilot: Any, value: str) -> None:
    input_widget = app.query_one("#prompt-input", Input)
    input_widget.focus()
    input_widget.value = value
    await pilot.press("enter")
    for _ in range(40):
        if not app.turn_running:
            return
        await pilot.pause(0.05)
    raise AssertionError("turn did not finish")


def load_resumed_state(store: TuiSessionStore, cwd: Path) -> TuiSessionState:
    result = store.load_latest(cwd=cwd)
    assert result.error is None
    assert result.state is not None
    return result.state


@pytest.mark.asyncio
async def test_tui_todo_survives_resume_and_reaches_provider_context(
    tmp_path: Path,
) -> None:
    settings = make_settings()
    store = make_store(tmp_path)
    first_app = CodeGopherApp(
        settings=settings,
        cwd=tmp_path,
        provider_factory=lambda _settings: MockProvider([[{"type": "done"}]]),
        session_store=store,
    )

    async with first_app.run_test() as pilot:
        await submit(first_app, pilot, "/todo add Resume TODO context")

    resumed_state = load_resumed_state(store, tmp_path)
    second_provider = MockProvider(
        [[{"type": "text_delta", "content": "continued"}, {"type": "done"}]]
    )
    second_app = CodeGopherApp(
        settings=settings,
        cwd=tmp_path,
        provider_factory=lambda _settings: second_provider,
        session_store=store,
        session_state=resumed_state,
    )

    async with second_app.run_test() as pilot:
        await submit(second_app, pilot, "/todo")
        await submit(second_app, pilot, "continue")

    assert "Resume TODO context" in second_app.chat_messages[0]
    assert "Resume TODO context" in str(second_provider.calls[0][0]["content"])
