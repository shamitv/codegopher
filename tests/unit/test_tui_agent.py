from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from textual.widgets import Input

from codegopher.config.schema import ApprovalMode, ModelConfig, Settings
from codegopher.core.errors import ConfigurationError
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


async def submit(app: CodeGopherApp, pilot, value: str, *, pause: float = 0.1) -> None:
    input_widget = app.query_one("#prompt-input", Input)
    input_widget.focus()
    input_widget.value = value
    await pilot.press("enter")
    await pilot.pause(pause)
    for _ in range(20):
        if not app.turn_running:
            break
        await pilot.pause(0.05)


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


@pytest.mark.asyncio
async def test_tui_preserves_provider_context_across_submitted_turns(tmp_path: Path) -> None:
    provider = MockProvider(
        [
            [{"type": "text_delta", "content": "first answer"}, {"type": "done"}],
            [{"type": "text_delta", "content": "second answer"}, {"type": "done"}],
        ]
    )
    app = make_app(tmp_path, provider)

    async with app.run_test() as pilot:
        await submit(app, pilot, "first question")
        await submit(app, pilot, "second question")

        assert provider.calls[1][1:] == [
            {"role": "user", "content": "first question"},
            {"role": "assistant", "content": "first answer"},
            {"role": "user", "content": "second question"},
        ]


@pytest.mark.asyncio
async def test_tui_starts_mcp_before_agent_turn_and_cleans_up(tmp_path: Path) -> None:
    provider = MockProvider([[{"type": "text_delta", "content": "ok"}, {"type": "done"}]])
    events: list[str] = []

    class FakeTool:
        name = "mcp__local__echo"
        description = "Echo"
        parameters = {"type": "object", "properties": {}}
        requires_approval = True

        async def execute(self, arguments, context):
            raise AssertionError("not used")

    class FakeMcpManager:
        async def start(self):
            events.append("start")
            return self

        def register_tools(self, registry) -> None:
            events.append("register")
            registry.register(FakeTool())

        async def aclose(self) -> None:
            events.append("close")

    app = CodeGopherApp(
        settings=make_settings(),
        cwd=tmp_path,
        provider_factory=lambda _settings: provider,
        mcp_manager_factory=lambda _settings, _cwd: FakeMcpManager(),
    )

    async with app.run_test() as pilot:
        assert events == ["start", "register"]
        await submit(app, pilot, "question")
        assert "mcp__local__echo" in provider.calls[0][0]["content"]

    assert events == ["start", "register", "close"]


@pytest.mark.asyncio
async def test_tui_disables_input_on_mcp_startup_failure(tmp_path: Path) -> None:
    provider = MockProvider([[{"type": "text_delta", "content": "ok"}, {"type": "done"}]])

    class FakeMcpManager:
        async def start(self):
            raise ConfigurationError("MCP server local failed to initialize")

        def register_tools(self, registry) -> None:
            raise AssertionError("not reached")

        async def aclose(self) -> None:
            pass

    app = CodeGopherApp(
        settings=make_settings(),
        cwd=tmp_path,
        provider_factory=lambda _settings: provider,
        mcp_manager_factory=lambda _settings, _cwd: FakeMcpManager(),
    )

    async with app.run_test():
        input_widget = app.query_one("#prompt-input", Input)

        assert input_widget.disabled is True
        assert app.chat_messages == ["MCP initialization failed: MCP server local failed to initialize"]
        assert app.status_message == "MCP initialization failed: MCP server local failed to initialize"


@pytest.mark.asyncio
async def test_tui_clear_keeps_provider_context_for_future_turns(tmp_path: Path) -> None:
    provider = MockProvider(
        [
            [{"type": "text_delta", "content": "first answer"}, {"type": "done"}],
            [{"type": "text_delta", "content": "second answer"}, {"type": "done"}],
        ]
    )
    app = make_app(tmp_path, provider)

    async with app.run_test() as pilot:
        await submit(app, pilot, "first question")
        await submit(app, pilot, "/clear")
        await submit(app, pilot, "second question")

        assert app.chat_messages == ["You: second question", "Assistant: second answer"]
        assert provider.calls[1][1:] == [
            {"role": "user", "content": "first question"},
            {"role": "assistant", "content": "first answer"},
            {"role": "user", "content": "second question"},
        ]


@pytest.mark.asyncio
async def test_tui_slash_commands_do_not_enter_provider_context(tmp_path: Path) -> None:
    provider = MockProvider(
        [
            [{"type": "text_delta", "content": "first answer"}, {"type": "done"}],
            [{"type": "text_delta", "content": "second answer"}, {"type": "done"}],
        ]
    )
    app = make_app(tmp_path, provider)

    async with app.run_test() as pilot:
        await submit(app, pilot, "first question")
        await submit(app, pilot, "/stats")
        await submit(app, pilot, "second question")

        provider_contents = [
            message.get("content")
            for message in provider.calls[1][1:]
            if message["role"] in {"user", "assistant"}
        ]
        assert provider_contents == ["first question", "first answer", "second question"]
        assert all("Stats:" not in str(content) for content in provider_contents)


@pytest.mark.asyncio
async def test_tui_preserves_tool_call_history_for_future_turns(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("project notes", encoding="utf-8")
    provider = MockProvider(
        [
            [
                {
                    "type": "tool_call",
                    "tool_call": {
                        "id": "call-1",
                        "name": "read_file",
                        "arguments": {"path": "README.md"},
                    },
                },
                {"type": "done"},
            ],
            [{"type": "text_delta", "content": "read complete"}, {"type": "done"}],
            [{"type": "text_delta", "content": "second answer"}, {"type": "done"}],
        ]
    )
    app = CodeGopherApp(
        settings=Settings(approval_mode=ApprovalMode.yolo),
        cwd=tmp_path,
        provider_factory=lambda _settings: provider,
    )

    async with app.run_test() as pilot:
        await submit(app, pilot, "read the file")
        await submit(app, pilot, "what did you read?")

        messages = provider.calls[2][1:]
        assert messages[1]["role"] == "assistant"
        assert messages[1]["tool_calls"][0]["function"]["name"] == "read_file"
        assert messages[2] == {
            "role": "tool",
            "tool_call_id": "call-1",
            "content": "project notes",
        }
        assert messages[4] == {"role": "user", "content": "what did you read?"}


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
