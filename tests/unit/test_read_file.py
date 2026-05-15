from __future__ import annotations

from pathlib import Path

import pytest

from codegopher.tools.base import ToolContext
from codegopher.tools.fs.read_file import ReadFileTool


@pytest.mark.asyncio
async def test_read_file_reads_utf8_text(tmp_path: Path) -> None:
    (tmp_path / "hello.txt").write_text("hello\nworld\n", encoding="utf-8")
    context = ToolContext(cwd=tmp_path)

    result = await ReadFileTool().execute({"path": "hello.txt"}, context)

    assert result.content == "hello\nworld"
    assert result.is_error is False


@pytest.mark.asyncio
async def test_read_file_supports_line_bounds(tmp_path: Path) -> None:
    (tmp_path / "hello.txt").write_text("one\ntwo\nthree\n", encoding="utf-8")
    context = ToolContext(cwd=tmp_path)

    result = await ReadFileTool().execute(
        {"path": "hello.txt", "start_line": 2, "end_line": 3},
        context,
    )

    assert result.content == "two\nthree"
