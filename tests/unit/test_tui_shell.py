from __future__ import annotations

import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
from textual.containers import Vertical
from textual.widgets import Input

from codegopher.config.schema import ApprovalMode, ModelConfig, Settings
from codegopher.core.approval import ApprovalResult
from codegopher.providers.mock import MockProvider
from codegopher.tui import CodeGopherApp


def make_settings(approval_mode: ApprovalMode) -> Settings:
    return Settings(
        model=ModelConfig(provider="openai", name="test-model"),
        approval_mode=approval_mode,
    )


def make_app(
    tmp_path: Path,
    approval_mode: ApprovalMode,
    *,
    shell_timeout_seconds: int = 30,
) -> tuple[CodeGopherApp, MockProvider]:
    provider = MockProvider([[{"type": "text_delta", "content": "unused"}, {"type": "done"}]])
    app = CodeGopherApp(
        settings=make_settings(approval_mode),
        cwd=tmp_path,
        provider_factory=lambda _settings: provider,
        shell_timeout_seconds=shell_timeout_seconds,
    )
    return app, provider


def python_command(source: str) -> str:
    if os.name == "nt":
        return subprocess.list2cmdline([sys.executable, "-c", source])
    return f"{shlex.quote(sys.executable)} -c {shlex.quote(source)}"


async def submit(app: CodeGopherApp, pilot: Any, value: str, *, pause: float = 0.1) -> None:
    input_widget = app.query_one("#prompt-input", Input)
    input_widget.focus()
    input_widget.value = value
    await pilot.press("enter")
    await pilot.pause(pause)


async def wait_for_shell(app: CodeGopherApp, pilot: Any) -> None:
    for _ in range(100):
        if not app.turn_running:
            return
        await pilot.pause(0.05)
    raise AssertionError("shell passthrough did not finish")


async def wait_for_approval(app: CodeGopherApp, pilot: Any) -> None:
    for _ in range(100):
        if (
            app._pending_approval is not None
            and app.query_one("#approval-panel", Vertical).display is True
        ):
            return
        await pilot.pause(0.05)
    raise AssertionError("approval prompt did not appear")


@pytest.mark.asyncio
async def test_tui_shell_requires_approval_and_renders_success(tmp_path: Path) -> None:
    app, provider = make_app(tmp_path, ApprovalMode.review)
    command = python_command("print('hello')")

    async with app.run_test() as pilot:
        await submit(app, pilot, f"/shell {command}")
        await wait_for_approval(app, pilot)

        assert len(provider.calls) == 0
        assert app.query_one("#approval-panel", Vertical).display is True
        assert app.chat_messages == [f"Shell requested: {command}"]

        await pilot.click("#approval-approve")
        await wait_for_shell(app, pilot)

        assert len(provider.calls) == 0
        assert any(message.startswith("Shell completed:") and "hello" in message for message in app.chat_messages)
        assert app.status_message == "Shell completed"


@pytest.mark.asyncio
async def test_tui_shell_denial_does_not_execute_subprocess(tmp_path: Path) -> None:
    app, provider = make_app(tmp_path, ApprovalMode.review)
    marker = tmp_path / "marker.txt"
    command = python_command("from pathlib import Path; Path('marker.txt').write_text('ran')")

    async with app.run_test() as pilot:
        await submit(app, pilot, f"/shell {command}")
        await wait_for_approval(app, pilot)
        app._resolve_pending_approval(ApprovalResult(approved=False, reason="Denied by user"))
        await wait_for_shell(app, pilot)

        assert len(provider.calls) == 0
        assert not marker.exists()
        assert "Shell denied: Denied by user" in app.chat_messages


@pytest.mark.asyncio
async def test_tui_shell_auto_mode_prompts_for_approval(tmp_path: Path) -> None:
    app, _provider = make_app(tmp_path, ApprovalMode.auto)
    command = python_command("print('auto')")

    async with app.run_test() as pilot:
        await submit(app, pilot, f"/shell {command}")
        await wait_for_approval(app, pilot)

        assert app.query_one("#approval-panel", Vertical).display is True
        assert app.approval_count == 1


@pytest.mark.asyncio
async def test_tui_shell_yolo_mode_skips_approval(tmp_path: Path) -> None:
    app, provider = make_app(tmp_path, ApprovalMode.yolo)
    command = python_command("print('yolo')")

    async with app.run_test() as pilot:
        await submit(app, pilot, f"/shell {command}")
        await wait_for_shell(app, pilot)

        assert len(provider.calls) == 0
        assert app.query_one("#approval-panel", Vertical).display is False
        assert app.approval_count == 0
        assert any("yolo" in message for message in app.chat_messages)


@pytest.mark.asyncio
async def test_tui_shell_renders_nonzero_exit(tmp_path: Path) -> None:
    app, _provider = make_app(tmp_path, ApprovalMode.yolo)
    command = python_command('import sys; print("bad"); sys.exit(3)')

    async with app.run_test() as pilot:
        await submit(app, pilot, f"/shell {command}")
        await wait_for_shell(app, pilot)

        assert any(
            message.startswith("Shell failed:")
            and "exit_code: 3" in message
            and "bad" in message
            for message in app.chat_messages
        )


@pytest.mark.asyncio
async def test_tui_shell_renders_timeout(tmp_path: Path) -> None:
    app, _provider = make_app(tmp_path, ApprovalMode.yolo, shell_timeout_seconds=1)
    command = python_command("import time; time.sleep(2)")

    async with app.run_test() as pilot:
        await submit(app, pilot, f"/shell {command}", pause=0.01)
        await wait_for_shell(app, pilot)

        assert any("timed out" in message for message in app.chat_messages)


@pytest.mark.asyncio
async def test_tui_shell_usage_error_does_not_call_provider(tmp_path: Path) -> None:
    app, provider = make_app(tmp_path, ApprovalMode.review)

    async with app.run_test() as pilot:
        await submit(app, pilot, "/shell")

        assert len(provider.calls) == 0
        assert app.chat_messages == ["Error: Usage: /shell COMMAND"]
