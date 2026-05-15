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

