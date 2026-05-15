from __future__ import annotations

from pathlib import Path

import pytest

from codegopher.tools.base import ToolContext
from codegopher.tools.fs.read_many_files import ReadManyFilesTool


@pytest.mark.asyncio
async def test_read_many_files_reads_paths_and_globs(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("alpha\n", encoding="utf-8")
    (tmp_path / "b.py").write_text("beta\n", encoding="utf-8")
    context = ToolContext(cwd=tmp_path)

    result = await ReadManyFilesTool().execute(
        {"paths": ["a.txt"], "globs": ["*.py"]},
        context,
    )

    assert "## a.txt\nalpha" in result.content
    assert "## b.py\nbeta" in result.content


@pytest.mark.asyncio
async def test_read_many_files_records_each_read(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("alpha\n", encoding="utf-8")
    (tmp_path / "b.txt").write_text("beta\n", encoding="utf-8")
    context = ToolContext(cwd=tmp_path)

    await ReadManyFilesTool().execute({"globs": ["*.txt"]}, context)

    assert context.access.has_read_file("a.txt")
    assert context.access.has_read_file("b.txt")
