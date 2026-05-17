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
async def test_tui_session_memory_survives_resume_and_can_be_forgotten(
    tmp_path: Path,
) -> None:
    settings = make_settings()
    store = make_store(tmp_path)
    first_provider = MockProvider(
        [
            [
                {
                    "type": "tool_call",
                    "tool_call": {
                        "id": "call-save",
                        "name": "save_memory",
                        "arguments": {
                            "scope": "session",
                            "content": "Integration session memory",
                        },
                    },
                },
                {"type": "done"},
            ],
            [{"type": "text_delta", "content": "saved"}, {"type": "done"}],
        ]
    )
    first_app = CodeGopherApp(
        settings=settings,
        cwd=tmp_path,
        provider_factory=lambda _settings: first_provider,
        session_store=store,
    )

    async with first_app.run_test() as pilot:
        await submit(first_app, pilot, "save this memory")

    resumed_state = load_resumed_state(store, tmp_path)
    second_provider = MockProvider(
        [[{"type": "text_delta", "content": "remembered"}, {"type": "done"}]]
    )
    second_app = CodeGopherApp(
        settings=settings,
        cwd=tmp_path,
        provider_factory=lambda _settings: second_provider,
        session_store=store,
        session_state=resumed_state,
    )

    async with second_app.run_test() as pilot:
        await submit(second_app, pilot, "what do you remember?")

        assert "Integration session memory" in str(second_provider.calls[0][0]["content"])
        assert second_app.tool_context.memory_store is not None
        entries = second_app.tool_context.memory_store.list_entries(
            "session",
            session_id=resumed_state.session_id,
        )
        assert len(entries) == 1

        await submit(second_app, pilot, f"/forget {entries[0].id} --yes")

    assert second_app.tool_context.memory_store is not None
    assert (
        second_app.tool_context.memory_store.list_entries(
            "session",
            session_id=resumed_state.session_id,
        )
        == []
    )
    assert any(message.startswith("Memory deleted:") for message in second_app.chat_messages)
