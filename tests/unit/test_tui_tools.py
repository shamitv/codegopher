from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from codegopher.config.schema import ApprovalMode, ModelConfig, Settings
from codegopher.providers.mock import MockProvider
from codegopher.tools.base import ToolContext, ToolResult
from codegopher.tools.registry import ToolRegistry, create_default_registry
from codegopher.tui import CodeGopherApp


def make_settings(approval_mode: ApprovalMode = ApprovalMode.yolo) -> Settings:
    return Settings(
        model=ModelConfig(provider="openai", name="test-model"),
        approval_mode=approval_mode,
    )


def make_registry(tool: FakeTool) -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(tool)
    return registry


@pytest.mark.asyncio
async def test_tui_renders_requested_tool_calls_with_argument_summary(tmp_path: Path) -> None:
    tool = FakeTool(name="inspect_project")
    provider = MockProvider(
        [
            [
                {
                    "type": "tool_call",
                    "tool_call": {
                        "id": "call-1",
                        "name": "inspect_project",
                        "arguments": {"path": "README.md"},
                    },
                },
                {"type": "done"},
            ],
            [{"type": "text_delta", "content": "done"}, {"type": "done"}],
        ]
    )
    app = CodeGopherApp(
        settings=make_settings(),
        cwd=tmp_path,
        provider_factory=lambda _settings: provider,
        registry_factory=lambda: make_registry(tool),
    )

    async with app.run_test() as pilot:
        app.query_one("#prompt-input").value = "inspect"

        await pilot.press("enter")
        await pilot.pause(0.1)

        assert any(
            message.startswith("Tool requested: inspect_project")
            and "README.md" in message
            for message in app.chat_messages
        )


@pytest.mark.asyncio
async def test_tui_renders_successful_tool_results(tmp_path: Path) -> None:
    tool = FakeTool(name="inspect_project")
    provider = MockProvider(
        [
            [
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
            [{"type": "text_delta", "content": "done"}, {"type": "done"}],
        ]
    )
    app = CodeGopherApp(
        settings=make_settings(),
        cwd=tmp_path,
        provider_factory=lambda _settings: provider,
        registry_factory=lambda: make_registry(tool),
    )

    async with app.run_test() as pilot:
        app.query_one("#prompt-input").value = "inspect"

        await pilot.press("enter")
        await pilot.pause(0.1)

        assert "Tool completed: inspect_project" in app.chat_messages


@pytest.mark.asyncio
async def test_tui_renders_failed_tool_results_with_content(tmp_path: Path) -> None:
    tool = FakeTool(name="inspect_project", result=ToolResult(tool_call_id="", content="boom", is_error=True))
    provider = MockProvider(
        [
            [
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
            [{"type": "text_delta", "content": "done"}, {"type": "done"}],
        ]
    )
    app = CodeGopherApp(
        settings=make_settings(),
        cwd=tmp_path,
        provider_factory=lambda _settings: provider,
        registry_factory=lambda: make_registry(tool),
    )

    async with app.run_test() as pilot:
        app.query_one("#prompt-input").value = "inspect"

        await pilot.press("enter")
        await pilot.pause(0.1)

        assert "Tool failed: inspect_project: boom" in app.chat_messages


@pytest.mark.asyncio
async def test_tui_keeps_filesystem_safety_errors_visible(tmp_path: Path) -> None:
    provider = MockProvider(
        [
            [
                {
                    "type": "tool_call",
                    "tool_call": {
                        "id": "call-1",
                        "name": "write_file",
                        "arguments": {"path": "new.txt", "content": "hello"},
                    },
                },
                {"type": "done"},
            ],
            [{"type": "text_delta", "content": "saw error"}, {"type": "done"}],
        ]
    )
    app = CodeGopherApp(
        settings=make_settings(),
        cwd=tmp_path,
        provider_factory=lambda _settings: provider,
        registry_factory=create_default_registry,
    )

    async with app.run_test() as pilot:
        app.query_one("#prompt-input").value = "write"

        await pilot.press("enter")
        await pilot.pause(0.1)

        assert any(
            message.startswith("Tool failed: write_file:")
            and "list_dir must inspect parent directory" in message
            for message in app.chat_messages
        )


class FakeTool:
    description = "Fake test tool"
    parameters: dict[str, Any] = {"type": "object", "properties": {}}

    def __init__(
        self,
        *,
        name: str = "fake_tool",
        requires_approval: bool = False,
        result: ToolResult | None = None,
    ) -> None:
        self.name = name
        self.requires_approval = requires_approval
        self.result = result
        self.executed = False

    async def execute(self, arguments: dict[str, Any], context: ToolContext) -> ToolResult:
        self.executed = True
        if self.result is not None:
            return ToolResult(
                tool_call_id=str(arguments.get("_tool_call_id", "")),
                content=self.result.content,
                is_error=self.result.is_error,
            )
        return ToolResult(tool_call_id=str(arguments.get("_tool_call_id", "")), content="ok")
