from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from textual.widgets import Static

from codegopher.config.schema import ApprovalMode, ModelConfig, Settings
from codegopher.providers.mock import MockProvider
from codegopher.tools.base import ToolContext, ToolResult
from codegopher.tools.registry import ToolRegistry
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

    async with app.run_test():
        await app._on_agent_reasoning_delta("thinking")

        assert app.query_one("#reasoning-stream", Static).display is True
        assert app._active_reasoning_message == "thinking"


@pytest.mark.asyncio
async def test_tui_handles_mixed_reasoning_answer_and_tool_call(tmp_path: Path) -> None:
    tool = FakeTool()
    registry = ToolRegistry()
    registry.register(tool)
    provider = MockProvider(
        [
            [
                {"type": "reasoning_delta", "content": "inspect first"},
                {"type": "text_delta", "content": "checking"},
                {
                    "type": "tool_call",
                    "tool_call": {
                        "id": "call-1",
                        "name": "inspect_project",
                        "arguments": {},
                    },
                },
                {"type": "done"},
            ],
            [{"type": "text_delta", "content": " done"}, {"type": "done"}],
        ]
    )
    app = CodeGopherApp(
        settings=Settings(
            model=ModelConfig(provider="openai", name="test-model"),
            approval_mode=ApprovalMode.yolo,
        ),
        cwd=tmp_path,
        provider_factory=lambda _settings: provider,
        registry_factory=lambda: registry,
    )

    async with app.run_test() as pilot:
        app.query_one("#prompt-input").value = "inspect"

        await pilot.press("enter")
        await pilot.pause(0.1)

        assert tool.executed is True
        assert "Tool requested: inspect_project" in app.chat_messages
        assert "Tool completed: inspect_project" in app.chat_messages
        assert "Reasoning (collapsed): inspect first" in app.chat_messages
        assert app.chat_messages[-1] == "Assistant: checking done"


class FakeTool:
    name = "inspect_project"
    description = "Fake inspection tool"
    parameters: dict[str, Any] = {"type": "object", "properties": {}}
    requires_approval = False

    def __init__(self) -> None:
        self.executed = False

    async def execute(self, arguments: dict[str, Any], context: ToolContext) -> ToolResult:
        self.executed = True
        return ToolResult(tool_call_id=str(arguments.get("_tool_call_id", "")), content="ok")
