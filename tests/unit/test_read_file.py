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


@pytest.mark.asyncio
async def test_read_file_reports_missing_file(tmp_path: Path) -> None:
    result = await ReadFileTool().execute({"path": "missing.txt"}, ToolContext(cwd=tmp_path))

    assert result.is_error is True


@pytest.mark.asyncio
async def test_read_file_reports_encoding_failures(tmp_path: Path) -> None:
    (tmp_path / "binary.bin").write_bytes(b"\xff\xfe\x00")

    result = await ReadFileTool().execute({"path": "binary.bin"}, ToolContext(cwd=tmp_path))

    assert result.is_error is True


@pytest.mark.asyncio
async def test_read_file_records_prior_read(tmp_path: Path) -> None:
    (tmp_path / "hello.txt").write_text("hello\n", encoding="utf-8")
    context = ToolContext(cwd=tmp_path)

    await ReadFileTool().execute({"path": "hello.txt"}, context)

    assert context.access.has_read_file("hello.txt")
