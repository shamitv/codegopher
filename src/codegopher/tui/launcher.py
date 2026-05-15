"""Launcher for CodeGopher's interactive terminal UI."""

from __future__ import annotations

from pathlib import Path

from codegopher.config.schema import Settings
from codegopher.tui.app import CodeGopherApp


def launch_tui(settings: Settings, *, cwd: Path) -> None:
    """Run the interactive terminal UI."""
    CodeGopherApp(settings=settings, cwd=cwd).run()
