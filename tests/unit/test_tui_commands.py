from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Callable
from pathlib import Path
from typing import Any

import pytest
from textual.containers import Vertical
from textual.widgets import Input

from codegopher.config.schema import ApprovalMode, ModelConfig, Settings
from codegopher.core.types import Message, StreamEvent, ToolSchema
from codegopher.providers.base import ProviderCapabilities
from codegopher.providers.mock import MockProvider
from codegopher.tools.base import ToolContext, ToolResult
from codegopher.tools.registry import ToolRegistry
from codegopher.tui import CodeGopherApp


def make_settings(
    *,
    model: str = "test-model",
    approval_mode: ApprovalMode = ApprovalMode.review,
) -> Settings:
    return Settings(
        model=ModelConfig(provider="openai", name=model),
        approval_mode=approval_mode,
    )


def make_app(
    tmp_path: Path,
    *,
    provider=None,
    settings: Settings | None = None,
    registry_factory: Callable[[], ToolRegistry] | None = None,
    clock: Callable[[], float] | None = None,
) -> CodeGopherApp:
    provider = provider or MockProvider([[{"type": "done"}]])
    return CodeGopherApp(
        settings=settings or make_settings(),
        cwd=tmp_path,
        provider_factory=lambda _settings: provider,
        registry_factory=registry_factory or ToolRegistry,
        clock=clock or (lambda: 0.0),
    )


async def submit_command(app: CodeGopherApp, pilot, value: str) -> None:
    input_widget = app.query_one("#prompt-input", Input)
    input_widget.focus()
    input_widget.value = value
    await pilot.press("enter")
    await pilot.pause(0.1)


@pytest.mark.asyncio
async def test_tui_help_command_renders_command_descriptions(tmp_path: Path) -> None:
    provider = MockProvider([[{"type": "done"}]])
    app = make_app(tmp_path, provider=provider)

    async with app.run_test() as pilot:
        await submit_command(app, pilot, "/help")

        assert len(provider.calls) == 0
        help_message = app.chat_messages[-1]
        for command in ("/help", "/clear", "/model", "/mode", "/stats"):
            assert command in help_message
        assert "show commands" in help_message
        assert app.status_message == "Help displayed"


@pytest.mark.asyncio
async def test_tui_clear_command_clears_visible_chat_without_changing_settings(
    tmp_path: Path,
) -> None:
    settings = make_settings(model="original-model", approval_mode=ApprovalMode.auto)
    app = make_app(tmp_path, settings=settings)

    async with app.run_test() as pilot:
        app.append_system_message("old message")

        await submit_command(app, pilot, "/clear")

        assert app.chat_messages == []
        assert app.settings.model.name == "original-model"
        assert app.settings.approval_mode is ApprovalMode.auto
        assert app.status_message == "Chat history cleared"


@pytest.mark.asyncio
async def test_tui_model_command_displays_active_provider_and_model(tmp_path: Path) -> None:
    app = make_app(tmp_path, settings=make_settings(model="display-model"))

    async with app.run_test() as pilot:
        await submit_command(app, pilot, "/model")

        assert app.chat_messages[-1] == "Model: openai/display-model"
        assert app.status_message == "Model displayed"


@pytest.mark.asyncio
async def test_tui_model_command_updates_model_for_next_provider_call(tmp_path: Path) -> None:
    provider = RecordingModelProvider()
    app = make_app(tmp_path, provider=provider, settings=make_settings(model="old-model"))

    async with app.run_test() as pilot:
        await submit_command(app, pilot, "/model new-model")

        assert "Model: new-model" in app.status_message

        await submit_command(app, pilot, "hello")

        assert app.settings.model.name == "new-model"
        assert provider.models == ["new-model"]
        assert "Model updated: openai/new-model" in app.chat_messages


@pytest.mark.asyncio
async def test_tui_mode_command_displays_active_approval_mode(tmp_path: Path) -> None:
    app = make_app(tmp_path, settings=make_settings(approval_mode=ApprovalMode.yolo))

    async with app.run_test() as pilot:
        await submit_command(app, pilot, "/mode")

        assert app.chat_messages[-1] == "Approval mode: yolo"
        assert app.status_message == "Approval mode displayed"


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", [ApprovalMode.review, ApprovalMode.auto, ApprovalMode.yolo])
async def test_tui_mode_command_updates_approval_mode(tmp_path: Path, mode: ApprovalMode) -> None:
    app = make_app(tmp_path, settings=make_settings(approval_mode=ApprovalMode.review))

    async with app.run_test() as pilot:
        await submit_command(app, pilot, f"/mode {mode.value}")

        assert app.settings.approval_mode is mode
        assert app.chat_messages[-1] == f"Approval mode updated: {mode.value}"
        assert f"Approval: {mode.value}" in app.status_message


@pytest.mark.asyncio
async def test_tui_mode_command_updates_future_approval_behavior(tmp_path: Path) -> None:
    tool = FakeTool(name="write_file", requires_approval=True)
    provider = MockProvider(
        [
            [
                {
                    "type": "tool_call",
                    "tool_call": {
                        "id": "call-1",
                        "name": "write_file",
                        "arguments": {},
                    },
                },
                {"type": "done"},
            ],
            [{"type": "text_delta", "content": "done"}, {"type": "done"}],
        ]
    )
    app = make_app(
        tmp_path,
        provider=provider,
        settings=make_settings(approval_mode=ApprovalMode.review),
        registry_factory=lambda: make_registry(tool),
    )

    async with app.run_test() as pilot:
        await submit_command(app, pilot, "/mode yolo")
        await submit_command(app, pilot, "write")

        assert tool.executed is True
        assert app.query_one("#approval-panel", Vertical).display is False


@pytest.mark.asyncio
async def test_tui_stats_command_renders_session_counters(tmp_path: Path) -> None:
    times = iter([100.0, 112.3])
    app = make_app(
        tmp_path,
        clock=lambda: next(times),
    )
    app.turn_count = 2
    app.tool_count = 3
    app.approval_count = 1

    async with app.run_test() as pilot:
        await submit_command(app, pilot, "/stats")

        assert app.chat_messages[-1] == (
            "Stats: turns=2, tools=3, approvals=1, elapsed=12.3s"
        )
        assert app.status_message == "Stats displayed"


@pytest.mark.asyncio
async def test_tui_stats_counters_increment_from_agent_activity(tmp_path: Path) -> None:
    times = iter([0.0, 5.0])
    tool = FakeTool(name="write_file", requires_approval=True)
    provider = MockProvider(
        [
            [
                {
                    "type": "tool_call",
                    "tool_call": {
                        "id": "call-1",
                        "name": "write_file",
                        "arguments": {},
                    },
                },
                {"type": "done"},
            ],
            [{"type": "text_delta", "content": "done"}, {"type": "done"}],
        ]
    )
    app = make_app(
        tmp_path,
        provider=provider,
        settings=make_settings(approval_mode=ApprovalMode.review),
        registry_factory=lambda: make_registry(tool),
        clock=lambda: next(times),
    )

    async with app.run_test() as pilot:
        await submit_command(app, pilot, "write")
        await pilot.click("#approval-approve")
        input_widget = app.query_one("#prompt-input", Input)
        for _ in range(10):
            await pilot.pause(0.1)
            if not input_widget.disabled:
                break

        assert input_widget.disabled is False

        await submit_command(app, pilot, "/stats")

        assert app.chat_messages[-1] == (
            "Stats: turns=1, tools=1, approvals=1, elapsed=5.0s"
        )


@pytest.mark.asyncio
async def test_tui_unknown_and_empty_slash_commands_render_errors(tmp_path: Path) -> None:
    provider = MockProvider([[{"type": "done"}]])
    app = make_app(tmp_path, provider=provider)

    async with app.run_test() as pilot:
        await submit_command(app, pilot, "/")
        await submit_command(app, pilot, "/wat")
        await submit_command(app, pilot, "/Help")

        assert len(provider.calls) == 0
        assert "Unknown command: /" in app.chat_messages
        assert "Unknown command: /wat" in app.chat_messages
        assert "Unknown command: /Help" in app.chat_messages
        assert app.status_message == "Unknown command: /Help"


@pytest.mark.asyncio
async def test_tui_slash_command_arguments_are_validated(tmp_path: Path) -> None:
    app = make_app(tmp_path)

    async with app.run_test() as pilot:
        await submit_command(app, pilot, "/clear now")
        await submit_command(app, pilot, "/model too many")
        await submit_command(app, pilot, "/mode careful")
        await submit_command(app, pilot, "/stats now")

        assert app.chat_messages == [
            "Unknown command: /clear",
            "Unknown command: /model",
            "Unknown command: /mode",
            "Unknown command: /stats",
        ]


@pytest.mark.asyncio
async def test_tui_commands_do_not_run_while_agent_turn_is_running(tmp_path: Path) -> None:
    provider = WaitingProvider()
    app = make_app(tmp_path, provider=provider)

    async with app.run_test() as pilot:
        app.query_one("#prompt-input", Input).value = "wait"

        await pilot.press("enter")
        await asyncio.wait_for(provider.started.wait(), timeout=1)
        await pilot.pause()

        assert app.query_one("#prompt-input", Input).disabled is True

        app.query_one("#prompt-input", Input).value = "/help"
        await pilot.press("enter")
        await pilot.pause()

        assert app.chat_messages == ["You: wait"]
        assert len(provider.calls) == 1

        provider.release.set()
        await pilot.pause(0.1)

        assert app.chat_messages == ["You: wait", "Assistant: done"]


def make_registry(tool: FakeTool) -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(tool)
    return registry


class FakeTool:
    description = "Fake test tool"
    parameters: dict[str, Any] = {"type": "object", "properties": {}}

    def __init__(self, *, name: str, requires_approval: bool) -> None:
        self.name = name
        self.requires_approval = requires_approval
        self.executed = False

    async def execute(self, arguments: dict[str, Any], context: ToolContext) -> ToolResult:
        self.executed = True
        return ToolResult(tool_call_id=str(arguments.get("_tool_call_id", "")), content="ok")


class RecordingModelProvider:
    capabilities = ProviderCapabilities(streaming=True, tool_calls=True)

    def __init__(self) -> None:
        self.models: list[str] = []

    async def stream(
        self,
        messages: list[Message],
        tools: list[ToolSchema],
        *,
        model: str,
        temperature: float,
        max_output_tokens: int,
    ) -> AsyncIterator[StreamEvent]:
        self.models.append(model)
        yield {"type": "text_delta", "content": "ok"}
        yield {"type": "done"}


class WaitingProvider:
    capabilities = ProviderCapabilities(streaming=True, tool_calls=True)

    def __init__(self) -> None:
        self.started = asyncio.Event()
        self.release = asyncio.Event()
        self.calls: list[list[Message]] = []

    async def stream(
        self,
        messages: list[Message],
        tools: list[ToolSchema],
        *,
        model: str,
        temperature: float,
        max_output_tokens: int,
    ) -> AsyncIterator[StreamEvent]:
        self.calls.append(messages)
        self.started.set()
        await self.release.wait()
        yield {"type": "text_delta", "content": "done"}
        yield {"type": "done"}
