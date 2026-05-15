from __future__ import annotations

from pathlib import Path

import pytest

from codegopher.tools.base import ToolContext
from codegopher.tools.shell.run_shell import RunShellCommandTool


@pytest.mark.asyncio
async def test_run_shell_command_captures_success(tmp_path: Path) -> None:
    result = await RunShellCommandTool().execute(
        {"command": "python -c \"print('hello')\""},
        ToolContext(cwd=tmp_path),
    )

    assert result.is_error is False
    assert "hello" in result.content


@pytest.mark.asyncio
async def test_run_shell_command_runs_in_context_cwd(tmp_path: Path) -> None:
    (tmp_path / "marker.txt").write_text("marker", encoding="utf-8")

    result = await RunShellCommandTool().execute(
        {"command": "python -c \"from pathlib import Path; print(Path('marker.txt').exists())\""},
        ToolContext(cwd=tmp_path),
    )

    assert "True" in result.content
