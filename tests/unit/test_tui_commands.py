from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

import pytest
from textual.containers import Vertical
from textual.widgets import Input

from codegopher.config.schema import ApprovalMode, ModelConfig, ProviderEntry, Settings
from codegopher.core.types import Message, StreamEvent, ToolSchema
from codegopher.providers.base import ProviderCapabilities
from codegopher.providers.mock import MockProvider
from codegopher.tools.base import ToolContext, ToolResult
from codegopher.tools.registry import ToolRegistry
from codegopher.tui import CodeGopherApp
from codegopher.tui.commands import SlashCommand, parse_slash_command


def make_settings(
    *,
    model_name: str = "test-model",
    approval_mode: ApprovalMode = ApprovalMode.auto,
) -> Settings:
    return Settings(
        model=ModelConfig(provider="openai", name=model_name),
        approval_mode=approval_mode,
    )


def make_app(
    tmp_path: Path,
    provider: Any | None = None,
    *,
    settings: Settings | None = None,
    registry: ToolRegistry | None = None,
    monotonic: Any | None = None,
) -> CodeGopherApp:
    active_provider = provider or MockProvider([[{"type": "text_delta", "content": "ok"}, {"type": "done"}]])
    kwargs: dict[str, Any] = {
        "settings": settings or make_settings(),
        "cwd": tmp_path,
        "provider_factory": lambda _settings: active_provider,
    }
    if registry is not None:
        kwargs["registry_factory"] = lambda: registry
    if monotonic is not None:
        kwargs["monotonic"] = monotonic
    return CodeGopherApp(**kwargs)


async def submit(app: CodeGopherApp, pilot: Any, value: str, *, pause: float = 0.1) -> Input:
    input_widget = app.query_one("#prompt-input", Input)
    input_widget.focus()
    input_widget.value = value
    await pilot.press("enter")
    await pilot.pause(pause)
    return input_widget


async def wait_for_turn_to_finish(app: CodeGopherApp, pilot: Any) -> None:
    for _ in range(20):
        if not app.turn_running:
            return
        await pilot.pause(0.05)
    raise AssertionError("agent turn did not finish")


def test_parse_slash_command_only_matches_slash_prefixed_input() -> None:
    assert parse_slash_command("hello") is None
    assert parse_slash_command("  hello /help") is None
    assert parse_slash_command("/model next-model") == SlashCommand(
        raw="/model next-model",
        name="model",
        arguments="next-model",
    )


@pytest.mark.asyncio
async def test_tui_help_command_lists_available_commands(tmp_path: Path) -> None:
    provider = MockProvider([[{"type": "done"}]])
    app = make_app(tmp_path, provider)

    async with app.run_test() as pilot:
        input_widget = await submit(app, pilot, "/help")

        assert input_widget.value == ""
        assert len(provider.calls) == 0
        assert app.status_message == "Displayed help"
        assert app.chat_messages[0].startswith("Slash commands:")
        assert "/help - Show available slash commands." in app.chat_messages[0]
        assert "/compact [instructions] - Compact provider context." in app.chat_messages[0]
        assert "/forget ID - Delete a memory after confirmation." in app.chat_messages[0]
        assert "/last - Jump to the last assistant response." in app.chat_messages[0]
        assert "/memory - List session and project memories." in app.chat_messages[0]
        assert "/skills [load ID] - List or load Markdown skills." in app.chat_messages[0]
        assert "/stats - Show session counters." in app.chat_messages[0]
        assert "/status - Show session and runtime status." in app.chat_messages[0]
        assert "/tools - Show tool activity from the last turn." in app.chat_messages[0]


@pytest.mark.asyncio
async def test_tui_clear_command_clears_visible_chat_history(tmp_path: Path) -> None:
    app = make_app(tmp_path)

    async with app.run_test() as pilot:
        app.append_system_message("Previous message")

        await submit(app, pilot, "/clear")

        assert app.chat_messages == []
        assert app.status_message == "Chat history cleared"


@pytest.mark.asyncio
async def test_tui_compact_command_accepts_optional_instructions_without_history(
    tmp_path: Path,
) -> None:
    provider = MockProvider([[{"type": "done"}]])
    app = make_app(tmp_path, provider)

    async with app.run_test() as pilot:
        await submit(app, pilot, "/compact focus on decisions")

        assert len(provider.calls) == 0
        assert app.chat_messages == ["Nothing to compact"]
        assert app.status_message == "Nothing to compact"


@pytest.mark.asyncio
async def test_tui_model_command_displays_active_model_and_provider(tmp_path: Path) -> None:
    app = make_app(tmp_path)

    async with app.run_test() as pilot:
        await submit(app, pilot, "/model")

        assert app.chat_messages == ["Model: test-model | Provider: openai"]
        assert app.status_message == "Displayed active model"


@pytest.mark.asyncio
async def test_tui_model_command_updates_future_agent_turns(tmp_path: Path) -> None:
    provider = RecordingProvider()
    app = make_app(tmp_path, provider)

    async with app.run_test() as pilot:
        await submit(app, pilot, "/model future-model")

        assert app.settings.model.name == "future-model"
        assert len(provider.models) == 0

        await submit(app, pilot, "hello")

        assert provider.models == ["future-model"]
        assert app.chat_messages[-1] == "Assistant: ok"


@pytest.mark.asyncio
async def test_tui_mode_command_displays_active_approval_mode(tmp_path: Path) -> None:
    app = make_app(tmp_path, settings=make_settings(approval_mode=ApprovalMode.review))

    async with app.run_test() as pilot:
        await submit(app, pilot, "/mode")

        assert app.chat_messages == ["Approval mode: review"]
        assert app.status_message == "Displayed approval mode"


@pytest.mark.parametrize("mode", [ApprovalMode.review, ApprovalMode.auto, ApprovalMode.yolo])
@pytest.mark.asyncio
async def test_tui_mode_command_updates_valid_approval_modes(
    tmp_path: Path,
    mode: ApprovalMode,
) -> None:
    app = make_app(tmp_path, settings=make_settings(approval_mode=ApprovalMode.review))

    async with app.run_test() as pilot:
        await submit(app, pilot, f"/mode {mode.value}")

        assert app.settings.approval_mode is mode
        assert app.chat_messages == [f"Approval mode updated: {mode.value}"]


@pytest.mark.asyncio
async def test_tui_mode_command_affects_future_agent_turns(tmp_path: Path) -> None:
    tool = FakeTool(name="write_file", requires_approval=True)
    registry = ToolRegistry()
    registry.register(tool)
    app = make_app(
        tmp_path,
        make_tool_call_provider(),
        settings=make_settings(approval_mode=ApprovalMode.review),
        registry=registry,
    )

    async with app.run_test() as pilot:
        await submit(app, pilot, "/mode yolo")
        await submit(app, pilot, "write")

        assert app.query_one("#approval-panel", Vertical).display is False
        assert tool.executed is True
        assert app.approval_count == 0


@pytest.mark.asyncio
async def test_tui_stats_command_reports_session_counters(tmp_path: Path) -> None:
    clock = FakeClock(100.0)
    tool = FakeTool(name="write_file", requires_approval=True)
    registry = ToolRegistry()
    registry.register(tool)
    provider = make_tool_call_provider()
    app = make_app(
        tmp_path,
        provider,
        settings=make_settings(approval_mode=ApprovalMode.review),
        registry=registry,
        monotonic=clock,
    )

    async with app.run_test() as pilot:
        await submit(app, pilot, "write")
        await pilot.click("#approval-approve")
        await wait_for_turn_to_finish(app, pilot)

        calls_before_stats = len(provider.calls)
        clock.value = 112.8
        await submit(app, pilot, "/stats")

        assert len(provider.calls) == calls_before_stats
        assert app.chat_messages[-1].startswith(
            "Stats: turns=1 | tools=1 | approvals=1 | elapsed=12s | "
            "memory=0 (session=0, project=0) | context="
        )
        assert app.chat_messages[-1].endswith("tokens (window unknown)")
        assert app.status_message == "Displayed stats"


@pytest.mark.asyncio
async def test_tui_stats_command_reports_known_context_budget(tmp_path: Path) -> None:
    settings = make_settings()
    settings.providers = {
        "openai": [
            ProviderEntry(id="test-model", name="Test Model", context_window=10_000)
        ]
    }
    provider = MockProvider([[{"type": "text_delta", "content": "answer"}, {"type": "done"}]])
    app = make_app(tmp_path, provider, settings=settings)

    async with app.run_test() as pilot:
        await submit(app, pilot, "hello")
        await wait_for_turn_to_finish(app, pilot)
        await submit(app, pilot, "/stats")

        assert "context=" in app.chat_messages[-1]
        assert "/10000 tokens" in app.chat_messages[-1]
        assert app.chat_messages[-1].endswith(", ok)")


@pytest.mark.asyncio
async def test_tui_status_command_reports_runtime_without_secret_values(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = make_settings(approval_mode=ApprovalMode.review)
    settings.providers = {
        "openai": [
            ProviderEntry(
                id="test-model",
                name="Test Model",
                base_url="https://user:raw-secret@example.test/v1?token=raw-secret",
                api_key_env="SECRET_API_KEY",
                context_window=10_000,
            )
        ]
    }
    monkeypatch.setenv("SECRET_API_KEY", "raw-secret")
    app = make_app(tmp_path, settings=settings)

    async with app.run_test() as pilot:
        await submit(app, pilot, "/status")

        status = app.chat_messages[-1]
        assert status.startswith("Status:\n")
        assert f"CWD: {tmp_path}" in status
        assert "Provider: openai" in status
        assert "Model: test-model" in status
        assert "Provider entry: Test Model (test-model)" in status
        assert "API family: chat_completions" in status
        assert "Base URL: https://[redacted]@example.test/v1" in status
        assert "API key env: SECRET_API_KEY" in status
        assert "Approval mode: review" in status
        assert "MCP: enabled | configured=0 | enabled=0 | connected_tools=0" in status
        assert "context=" in status
        assert "raw-secret" not in status
        assert "token=" not in status
        assert app.status_message == "Displayed status"


@pytest.mark.asyncio
async def test_tui_last_command_jumps_to_last_assistant_response(tmp_path: Path) -> None:
    provider = MockProvider([[{"type": "text_delta", "content": "answer"}, {"type": "done"}]])
    app = make_app(tmp_path, provider)

    async with app.run_test() as pilot:
        await submit(app, pilot, "hello")
        await wait_for_turn_to_finish(app, pilot)
        assert app._last_assistant_scroll_y is not None

        await submit(app, pilot, "/last")

        assert app.status_message == "Jumped to last assistant response"


@pytest.mark.asyncio
async def test_tui_last_command_reports_missing_assistant_response(tmp_path: Path) -> None:
    app = make_app(tmp_path)

    async with app.run_test() as pilot:
        await submit(app, pilot, "/last")

        assert app.chat_messages == ["No assistant response to jump to"]
        assert app.status_message == "No assistant response"


@pytest.mark.asyncio
async def test_tui_tools_command_reports_last_turn_details(tmp_path: Path) -> None:
    tool = FakeTool(name="write_file", requires_approval=False)
    registry = ToolRegistry()
    registry.register(tool)
    app = make_app(
        tmp_path,
        make_tool_call_provider(),
        settings=make_settings(approval_mode=ApprovalMode.yolo),
        registry=registry,
    )

    async with app.run_test() as pilot:
        await submit(app, pilot, "write")
        await wait_for_turn_to_finish(app, pilot)
        await submit(app, pilot, "/tools")

        assert app.chat_messages[-1].startswith("Tools from last turn:\n")
        assert "- write_file [completed]" in app.chat_messages[-1]
        assert "new.txt" in app.chat_messages[-1]
        assert "result=ok" in app.chat_messages[-1]
        assert app.status_message == "Displayed tools"


@pytest.mark.asyncio
async def test_tui_tools_command_reports_no_last_turn_tools(tmp_path: Path) -> None:
    app = make_app(tmp_path)

    async with app.run_test() as pilot:
        await submit(app, pilot, "/tools")

        assert app.chat_messages == ["Tools: none in the last turn"]
        assert app.status_message == "Displayed tools"


@pytest.mark.asyncio
async def test_tui_unknown_slash_command_renders_error(tmp_path: Path) -> None:
    provider = MockProvider([[{"type": "done"}]])
    app = make_app(tmp_path, provider)

    async with app.run_test() as pilot:
        await submit(app, pilot, "/wat")

        assert len(provider.calls) == 0
        assert app.chat_messages == ["Error: Unknown slash command: /wat"]
        assert app.status_message == "Error: Unknown slash command: /wat"


@pytest.mark.parametrize(
    "command",
    [
        "/help",
        "/clear",
        "/forget",
        "/last",
        "/model",
        "/model next-model",
        "/mode",
        "/mode yolo",
        "/memory",
        "/skills",
        "/skills load missing",
        "/stats",
        "/status",
        "/todo",
        "/tools",
        "/unknown",
    ],
)
@pytest.mark.asyncio
async def test_tui_slash_commands_do_not_call_provider(
    tmp_path: Path,
    command: str,
) -> None:
    provider = MockProvider([[{"type": "done"}]])
    app = make_app(tmp_path, provider)

    async with app.run_test() as pilot:
        await submit(app, pilot, command)

        assert len(provider.calls) == 0
        assert app.turn_count == 0


class RecordingProvider:
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


class FakeClock:
    def __init__(self, value: float) -> None:
        self.value = value

    def __call__(self) -> float:
        return self.value


def make_tool_call_provider() -> MockProvider:
    return MockProvider(
        [
            [
                {
                    "type": "tool_call",
                    "tool_call": {
                        "id": "call-1",
                        "name": "write_file",
                        "arguments": {"path": "new.txt"},
                    },
                },
                {"type": "done"},
            ],
            [{"type": "text_delta", "content": "finished"}, {"type": "done"}],
        ]
    )


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
