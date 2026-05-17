from __future__ import annotations

import os
import shlex
import subprocess
import sys
from pathlib import Path

import pytest

from codegopher.tools.base import ToolContext
from codegopher.tools.shell.run_shell import RunShellCommandTool


def python_command(source: str) -> str:
    if os.name == "nt":
        return subprocess.list2cmdline([sys.executable, "-c", source])
    return f"{shlex.quote(sys.executable)} -c {shlex.quote(source)}"


@pytest.mark.asyncio
async def test_run_shell_command_captures_success(tmp_path: Path) -> None:
    result = await RunShellCommandTool().execute(
        {"command": python_command("print('hello')")},
        ToolContext(cwd=tmp_path),
    )

    assert result.is_error is False
    assert "hello" in result.content


@pytest.mark.asyncio
async def test_run_shell_command_runs_in_context_cwd(tmp_path: Path) -> None:
    (tmp_path / "marker.txt").write_text("marker", encoding="utf-8")

    result = await RunShellCommandTool().execute(
        {"command": python_command("from pathlib import Path; print(Path('marker.txt').exists())")},
        ToolContext(cwd=tmp_path),
    )

    assert "True" in result.content


@pytest.mark.asyncio
async def test_run_shell_command_reports_nonzero_exit(tmp_path: Path) -> None:
    result = await RunShellCommandTool().execute(
        {"command": python_command("import sys; print('bad'); sys.exit(3)")},
        ToolContext(cwd=tmp_path),
    )

    assert result.is_error is True
    assert "exit_code: 3" in result.content
    assert "bad" in result.content


@pytest.mark.asyncio
async def test_run_shell_command_reports_timeout(tmp_path: Path) -> None:
    result = await RunShellCommandTool().execute(
        {"command": python_command("import time; time.sleep(2)"), "timeout_seconds": 1},
        ToolContext(cwd=tmp_path),
    )

    assert result.is_error is True
    assert "timed out" in result.content


def test_run_shell_command_requires_approval() -> None:
    assert RunShellCommandTool.requires_approval is True
