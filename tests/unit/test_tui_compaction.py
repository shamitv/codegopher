from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from textual.widgets import Input

from codegopher.config.schema import ApprovalMode, ModelConfig, Settings
from codegopher.core.types import Message
from codegopher.providers.mock import MockProvider
from codegopher.tui import CodeGopherApp
from codegopher.tui.session import TuiSessionStore


def make_settings() -> Settings:
    return Settings(
        model=ModelConfig(provider="openai", name="test-model"),
        approval_mode=ApprovalMode.yolo,
    )


async def submit(app: CodeGopherApp, pilot: Any, value: str) -> None:
    input_widget = app.query_one("#prompt-input", Input)
    input_widget.focus()
    input_widget.value = value
    await pilot.press("enter")
    for _ in range(40):
        if not app.turn_running:
            break
        await pilot.pause(0.05)


def provider_history() -> list[Message]:
    return [
        {"role": "user", "content": "first question"},
        {"role": "assistant", "content": "first answer"},
        {"role": "user", "content": "second question"},
        {"role": "assistant", "content": "second answer"},
        {"role": "user", "content": "third question"},
        {"role": "assistant", "content": "third answer"},
    ]


@pytest.mark.asyncio
async def test_tui_manual_compaction_persists_visible_summary(tmp_path: Path) -> None:
    store = TuiSessionStore(data_home=tmp_path / "data")
    state = store.create(cwd=tmp_path, settings=make_settings())
    state.provider_messages = provider_history()
    provider = MockProvider(
        [[{"type": "text_delta", "content": "summary text"}, {"type": "done"}]]
    )
    app = CodeGopherApp(
        settings=make_settings(),
        cwd=tmp_path,
        provider_factory=lambda _settings: provider,
        session_store=store,
        session_state=state,
    )

    async with app.run_test() as pilot:
        await submit(app, pilot, "/compact focus on decisions")

    assert "focus on decisions" in str(provider.calls[0][-1]["content"])
    assert app.chat_messages[-1] == "Context compacted (manual): summary text"
    assert state.provider_messages[0]["role"] == "system"
    assert "summary text" in str(state.provider_messages[0]["content"])
    assert "second question" in [
        message.get("content") for message in state.provider_messages
    ]
    assert "first question" not in [
        message.get("content") for message in state.provider_messages
    ]


@pytest.mark.asyncio
async def test_tui_manual_compaction_failure_preserves_session_context(
    tmp_path: Path,
) -> None:
    store = TuiSessionStore(data_home=tmp_path / "data")
    state = store.create(cwd=tmp_path, settings=make_settings())
    original = provider_history()
    state.provider_messages = list(original)
    provider = MockProvider([[{"type": "error", "message": "provider failed"}]])
    app = CodeGopherApp(
        settings=make_settings(),
        cwd=tmp_path,
        provider_factory=lambda _settings: provider,
        session_store=store,
        session_state=state,
    )

    async with app.run_test() as pilot:
        await submit(app, pilot, "/compact")

    assert app.chat_messages[-1] == "Compaction failed: provider failed"
    assert app.status_message == "Compaction failed: provider failed"
    assert state.provider_messages == original
