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
            break
        await pilot.pause(0.05)


def load_resumed_state(store: TuiSessionStore, cwd: Path) -> TuiSessionState:
    result = store.load_latest(cwd=cwd)
    assert result.error is None
    assert result.state is not None
    return result.state


@pytest.mark.asyncio
async def test_tui_resume_sends_prior_provider_history_to_next_turn(tmp_path: Path) -> None:
    store = make_store(tmp_path)
    first_provider = MockProvider(
        [[{"type": "text_delta", "content": "earlier answer"}, {"type": "done"}]]
    )
    first_app = CodeGopherApp(
        settings=make_settings(),
        cwd=tmp_path,
        provider_factory=lambda _settings: first_provider,
        session_store=store,
    )

    async with first_app.run_test() as pilot:
        await submit(first_app, pilot, "earlier question")

    resumed_state = load_resumed_state(store, tmp_path)
    second_provider = MockProvider(
        [[{"type": "text_delta", "content": "new answer"}, {"type": "done"}]]
    )
    second_app = CodeGopherApp(
        settings=make_settings(),
        cwd=tmp_path,
        provider_factory=lambda _settings: second_provider,
        session_store=store,
        session_state=resumed_state,
    )

    async with second_app.run_test() as pilot:
        await submit(second_app, pilot, "new question")

    assert second_provider.calls[0][1:] == [
        {"role": "user", "content": "earlier question"},
        {"role": "assistant", "content": "earlier answer"},
        {"role": "user", "content": "new question"},
    ]


@pytest.mark.asyncio
async def test_tui_resume_does_not_restore_file_access_grants(tmp_path: Path) -> None:
    (tmp_path / "existing.txt").write_text("old", encoding="utf-8")
    store = make_store(tmp_path)
    first_provider = MockProvider(
        [
            [
                {
                    "type": "tool_call",
                    "tool_call": {
                        "id": "call-read",
                        "name": "read_file",
                        "arguments": {"path": "existing.txt"},
                    },
                },
                {"type": "done"},
            ],
            [{"type": "text_delta", "content": "read complete"}, {"type": "done"}],
        ]
    )
    first_app = CodeGopherApp(
        settings=make_settings(),
        cwd=tmp_path,
        provider_factory=lambda _settings: first_provider,
        session_store=store,
    )

    async with first_app.run_test() as pilot:
        await submit(first_app, pilot, "read existing.txt")

    resumed_state = load_resumed_state(store, tmp_path)
    second_provider = MockProvider(
        [
            [
                {
                    "type": "tool_call",
                    "tool_call": {
                        "id": "call-write",
                        "name": "write_file",
                        "arguments": {"path": "existing.txt", "content": "new"},
                    },
                },
                {"type": "done"},
            ],
            [{"type": "text_delta", "content": "write attempted"}, {"type": "done"}],
        ]
    )
    second_app = CodeGopherApp(
        settings=make_settings(),
        cwd=tmp_path,
        provider_factory=lambda _settings: second_provider,
        session_store=store,
        session_state=resumed_state,
    )

    async with second_app.run_test() as pilot:
        await submit(second_app, pilot, "write existing.txt")

    assert (tmp_path / "existing.txt").read_text(encoding="utf-8") == "old"
    assert second_provider.calls[1][-1]["role"] == "tool"
    assert "must read it first" in str(second_provider.calls[1][-1]["content"])
