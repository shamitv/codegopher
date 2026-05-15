"""Launcher for CodeGopher's interactive terminal UI."""

from __future__ import annotations

from pathlib import Path

from codegopher.config.schema import Settings
from codegopher.tui.app import CodeGopherApp
from codegopher.tui.session import TuiSessionStore


def launch_tui(settings: Settings, *, cwd: Path) -> None:
    """Run the interactive terminal UI."""
    session_store = TuiSessionStore.default()
    load_result = session_store.load_latest(cwd=cwd)
    CodeGopherApp(
        settings=settings,
        cwd=cwd,
        session_store=session_store,
        session_state=load_result.state,
        session_load_error=load_result.error,
    ).run()
