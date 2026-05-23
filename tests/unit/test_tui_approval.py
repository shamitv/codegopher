from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from textual.containers import Vertical
from textual.widgets import Input

from codegopher.config.schema import ApprovalMode, ModelConfig, Settings
from codegopher.providers.mock import MockProvider
from codegopher.tools.base import ToolContext, ToolResult
from codegopher.tools.registry import ToolRegistry
from codegopher.tui import CodeGopherApp


def make_settings(approval_mode: ApprovalMode) -> Settings:
    return Settings(
        model=ModelConfig(provider="openai", name="test-model"),
        approval_mode=approval_mode,
    )


def make_registry(tool: FakeTool) -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(tool)
    return registry


def make_provider(tool_name: str = "write_file") -> MockProvider:
    return MockProvider(
        [
            [
                {
                    "type": "tool_call",
                    "tool_call": {
                        "id": "call-1",
                        "name": tool_name,
                        "arguments": {"path": "new.txt"},
                    },
                },
                {"type": "done"},
            ],
            [{"type": "text_delta", "content": "finished"}, {"type": "done"}],
        ]
    )


@pytest.mark.asyncio
async def test_tui_review_mode_prompts_for_required_tools(tmp_path: Path) -> None:
    tool = FakeTool(name="write_file", requires_approval=True)
    app = CodeGopherApp(
        settings=make_settings(ApprovalMode.review),
        cwd=tmp_path,
        provider_factory=lambda _settings: make_provider(),
        registry_factory=lambda: make_registry(tool),
    )

    async with app.run_test() as pilot:
        app.query_one("#prompt-input", Input).value = "write"

        await pilot.press("enter")
        await pilot.pause(0.1)

        assert app.query_one("#approval-panel", Vertical).display is True
        assert "Approval required: write_file" in app.status_message

        await pilot.click("#approval-approve")
        await pilot.pause(0.1)

        assert tool.executed is True
        assert app.query_one("#approval-panel", Vertical).display is False
        assert "Tools used: 1 (1 completed) - write_file. Run /tools for details." in app.chat_messages


@pytest.mark.asyncio
async def test_tui_deny_returns_denied_tool_result_to_model(tmp_path: Path) -> None:
    tool = FakeTool(name="write_file", requires_approval=True)
    provider = make_provider()
    app = CodeGopherApp(
        settings=make_settings(ApprovalMode.review),
        cwd=tmp_path,
        provider_factory=lambda _settings: provider,
        registry_factory=lambda: make_registry(tool),
    )

    async with app.run_test() as pilot:
        app.query_one("#prompt-input", Input).value = "write"

        await pilot.press("enter")
        await pilot.pause(0.1)
        await pilot.click("#approval-deny")
        await pilot.pause(0.1)

        assert tool.executed is False
        assert "Tool failed: write_file: Denied by user" in app.chat_messages
        assert provider.calls[1][-1]["content"] == "Denied by user"


@pytest.mark.asyncio
async def test_tui_deny_uses_reason_when_provided(tmp_path: Path) -> None:
    tool = FakeTool(name="write_file", requires_approval=True)
    provider = make_provider()
    app = CodeGopherApp(
        settings=make_settings(ApprovalMode.review),
        cwd=tmp_path,
        provider_factory=lambda _settings: provider,
        registry_factory=lambda: make_registry(tool),
    )

    async with app.run_test() as pilot:
        app.query_one("#prompt-input", Input).value = "write"

        await pilot.press("enter")
        await pilot.pause(0.1)
        app.query_one("#approval-reason", Input).value = "too risky"
        await pilot.click("#approval-deny")
        await pilot.pause(0.1)

        assert tool.executed is False
        assert "Tool failed: write_file: too risky" in app.chat_messages
        assert provider.calls[1][-1]["content"] == "too risky"


@pytest.mark.asyncio
async def test_tui_auto_mode_prompts_for_read_only_tools(tmp_path: Path) -> None:
    tool = FakeTool(name="read_file", requires_approval=False)
    app = CodeGopherApp(
        settings=make_settings(ApprovalMode.auto),
        cwd=tmp_path,
        provider_factory=lambda _settings: make_provider("read_file"),
        registry_factory=lambda: make_registry(tool),
    )

    async with app.run_test() as pilot:
        app.query_one("#prompt-input", Input).value = "read"

        await pilot.press("enter")
        await pilot.pause(0.1)

        assert app.query_one("#approval-panel", Vertical).display is True

        await pilot.click("#approval-approve")
        await pilot.pause(0.1)

        assert tool.executed is True


@pytest.mark.asyncio
async def test_tui_yolo_mode_skips_approval_ui(tmp_path: Path) -> None:
    tool = FakeTool(name="write_file", requires_approval=True)
    app = CodeGopherApp(
        settings=make_settings(ApprovalMode.yolo),
        cwd=tmp_path,
        provider_factory=lambda _settings: make_provider(),
        registry_factory=lambda: make_registry(tool),
    )

    async with app.run_test() as pilot:
        app.query_one("#prompt-input", Input).value = "write"

        await pilot.press("enter")
        await pilot.pause(0.1)

        assert app.query_one("#approval-panel", Vertical).display is False
        assert tool.executed is True
        assert "Tools used: 1 (1 completed) - write_file. Run /tools for details." in app.chat_messages


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
