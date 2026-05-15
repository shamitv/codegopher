from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from textual.widgets import Input

from codegopher.config.schema import ApprovalMode, ModelConfig, Settings
from codegopher.core.types import Message, StreamEvent, ToolSchema
from codegopher.providers.base import ProviderCapabilities
from codegopher.providers.mock import MockProvider
from codegopher.tui import CodeGopherApp


def make_settings() -> Settings:
    return Settings(
        model=ModelConfig(provider="openai", name="test-model"),
        approval_mode=ApprovalMode.auto,
    )


def make_app(tmp_path: Path, provider) -> CodeGopherApp:
    return CodeGopherApp(
        settings=make_settings(),
        cwd=tmp_path,
        provider_factory=lambda _settings: provider,
    )


@pytest.mark.asyncio
async def test_tui_submitted_input_streams_agent_text(tmp_path: Path) -> None:
    provider = MockProvider(
        [[{"type": "text_delta", "content": "hel"}, {"type": "text_delta", "content": "lo"}, {"type": "done"}]]
    )
    app = make_app(tmp_path, provider)

    async with app.run_test() as pilot:
        input_widget = app.query_one("#prompt-input", Input)
        input_widget.value = "say hello"

        await pilot.press("enter")
        await pilot.pause(0.1)

        assert app.chat_messages == ["You: say hello", "Assistant: hello"]
        assert input_widget.disabled is False
        assert app.status_message == "Done after 1 iteration(s)"


@pytest.mark.asyncio
async def test_tui_input_is_disabled_while_agent_turn_runs(tmp_path: Path) -> None:
    provider = WaitingProvider()
    app = make_app(tmp_path, provider)

    async with app.run_test() as pilot:
        input_widget = app.query_one("#prompt-input", Input)
        input_widget.value = "wait"

        await pilot.press("enter")
        await asyncio.wait_for(provider.started.wait(), timeout=1)
        await pilot.pause()

        assert input_widget.disabled is True
        assert app.turn_running is True

        provider.release.set()
        await pilot.pause(0.1)

        assert input_widget.disabled is False
        assert app.turn_running is False
        assert app.chat_messages == ["You: wait", "Assistant: done"]


@pytest.mark.asyncio
async def test_tui_surfaces_provider_errors(tmp_path: Path) -> None:
    provider = MockProvider([[{"type": "error", "message": "provider failed"}]])
    app = make_app(tmp_path, provider)

    async with app.run_test() as pilot:
        input_widget = app.query_one("#prompt-input", Input)
        input_widget.value = "fail"

        await pilot.press("enter")
        await pilot.pause(0.1)

        assert "Error: provider failed" in app.status_message
        assert app.chat_messages == ["You: fail", "Error: provider failed"]
        assert input_widget.disabled is False


@pytest.mark.asyncio
async def test_tui_runs_integration_style_mock_provider_turn(tmp_path: Path) -> None:
    provider = MockProvider([[{"type": "text_delta", "content": "final answer"}, {"type": "done"}]])
    app = make_app(tmp_path, provider)

    async with app.run_test() as pilot:
        input_widget = app.query_one("#prompt-input", Input)
        input_widget.value = "question"

        await pilot.press("enter")
        await pilot.pause(0.1)

        assert app.chat_messages[-1] == "Assistant: final answer"
        assert provider.calls[0][-1]["content"] == "question"


class WaitingProvider:
    capabilities = ProviderCapabilities(streaming=True, tool_calls=True)

    def __init__(self) -> None:
        self.started = asyncio.Event()
        self.release = asyncio.Event()

    async def stream(
        self,
        messages: list[Message],
        tools: list[ToolSchema],
        *,
        model: str,
        temperature: float,
        max_output_tokens: int,
    ) -> AsyncIterator[StreamEvent]:
        self.started.set()
        await self.release.wait()
        yield {"type": "text_delta", "content": "done"}
        yield {"type": "done"}
