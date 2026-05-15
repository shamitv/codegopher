from __future__ import annotations

from pathlib import Path

import pytest

from codegopher.tools.base import ToolContext
from codegopher.tools.fs.write_file import WriteFileTool


@pytest.mark.asyncio
async def test_write_file_creates_new_file_after_parent_inspection(tmp_path: Path) -> None:
    context = ToolContext(cwd=tmp_path)
    context.access.record_directory_inspection(".")

    result = await WriteFileTool().execute({"path": "created.txt", "content": "hello"}, context)

    assert result.is_error is False
    assert (tmp_path / "created.txt").read_text(encoding="utf-8") == "hello"
    assert WriteFileTool.requires_approval is True

