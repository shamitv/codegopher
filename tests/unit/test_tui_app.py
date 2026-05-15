from __future__ import annotations

from pathlib import Path

import pytest
from textual.widgets import Input, RichLog, Static

from codegopher.config.schema import ApprovalMode, ModelConfig, Settings
from codegopher.tui import CodeGopherApp


def make_app(tmp_path: Path) -> CodeGopherApp:
    return CodeGopherApp(
        settings=Settings(
            model=ModelConfig(provider="openai", name="test-model"),
            approval_mode=ApprovalMode.auto,
        ),
        cwd=tmp_path,
    )


@pytest.mark.asyncio
async def test_tui_app_starts_with_expected_regions(tmp_path: Path) -> None:
    app = make_app(tmp_path)

    async with app.run_test() as pilot:
        await pilot.pause()

        assert app.query_one("#session-status", Static)
        assert app.query_one("#chat-history", RichLog)
        assert app.query_one("#prompt-input", Input)


@pytest.mark.asyncio
async def test_tui_app_renders_startup_status(tmp_path: Path) -> None:
    app = make_app(tmp_path)

    async with app.run_test() as pilot:
        await pilot.pause()

        status = app.status_message
        assert "Model: test-model" in status
        assert "Provider: openai" in status
        assert "Approval: auto" in status
        assert str(tmp_path) in status


@pytest.mark.asyncio
async def test_tui_app_appends_submitted_input(tmp_path: Path) -> None:
    app = make_app(tmp_path)

    async with app.run_test() as pilot:
        input_widget = app.query_one("#prompt-input", Input)
        input_widget.focus()
        input_widget.value = "hello tui"

        await pilot.press("enter")
        await pilot.pause()

        assert app.chat_messages == ["You: hello tui"]
        assert input_widget.value == ""
        assert "agent streaming starts" in app.status_message


@pytest.mark.asyncio
async def test_tui_app_handles_empty_submit_as_status_message(tmp_path: Path) -> None:
    app = make_app(tmp_path)

    async with app.run_test() as pilot:
        input_widget = app.query_one("#prompt-input", Input)
        input_widget.focus()

        await pilot.press("enter")
        await pilot.pause()

        assert app.chat_messages == []
        assert app.status_message == "Enter a prompt to continue"


@pytest.mark.asyncio
async def test_tui_app_focus_binding_updates_status(tmp_path: Path) -> None:
    app = make_app(tmp_path)

    async with app.run_test() as pilot:
        await pilot.press("ctrl+i")
        await pilot.pause()

        assert app.query_one("#prompt-input", Input).has_focus
        assert app.status_message == "Input focused"


def test_tui_app_exposes_required_bindings() -> None:
    binding_keys = {binding[0] for binding in CodeGopherApp.BINDINGS if isinstance(binding, tuple)}

    assert "ctrl+q" in binding_keys
    assert "ctrl+i" in binding_keys
