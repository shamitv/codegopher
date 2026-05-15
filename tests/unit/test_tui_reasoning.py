from __future__ import annotations

from pathlib import Path

import pytest
from textual.widgets import Static

from codegopher.config.schema import ApprovalMode, ModelConfig, Settings
from codegopher.providers.mock import MockProvider
from codegopher.tui import CodeGopherApp


def make_app(tmp_path: Path, provider: MockProvider) -> CodeGopherApp:
    return CodeGopherApp(
        settings=Settings(
            model=ModelConfig(provider="openai", name="test-model"),
            approval_mode=ApprovalMode.yolo,
        ),
        cwd=tmp_path,
        provider_factory=lambda _settings: provider,
    )


@pytest.mark.asyncio
async def test_tui_renders_reasoning_collapsed_and_separate_from_answer(tmp_path: Path) -> None:
    provider = MockProvider(
        [
            [
                {"type": "reasoning_delta", "content": "think"},
                {"type": "text_delta", "content": "answer"},
                {"type": "done"},
            ]
        ]
    )
    app = make_app(tmp_path, provider)

    async with app.run_test() as pilot:
        input_widget = app.query_one("#prompt-input")
        input_widget.value = "reason"

        await pilot.press("enter")
        await pilot.pause(0.1)

        assert app.query_one("#reasoning-stream", Static).display is False
        assert app.chat_messages == [
            "You: reason",
            "Reasoning (collapsed): think",
            "Assistant: answer",
        ]


@pytest.mark.asyncio
async def test_tui_reasoning_indicator_is_collapsed_during_turn(tmp_path: Path) -> None:
    provider = MockProvider([[{"type": "done"}]])
    app = make_app(tmp_path, provider)

    async with app.run_test() as pilot:
        await app._on_agent_reasoning_delta("thinking")

        assert app.query_one("#reasoning-stream", Static).display is True
        assert app._active_reasoning_message == "thinking"
