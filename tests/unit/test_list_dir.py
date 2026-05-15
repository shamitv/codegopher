from __future__ import annotations

from pathlib import Path

import pytest

from codegopher.tools.base import ToolContext
from codegopher.tools.fs.list_dir import ListDirTool


@pytest.mark.asyncio
async def test_list_dir_lists_entries(tmp_path: Path) -> None:
    (tmp_path / "b.txt").write_text("b", encoding="utf-8")
    (tmp_path / "a").mkdir()

    result = await ListDirTool().execute({"path": "."}, ToolContext(cwd=tmp_path))

    assert result.content == "a/\nb.txt"


@pytest.mark.asyncio
async def test_list_dir_records_directory_inspection(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    context = ToolContext(cwd=tmp_path)

    await ListDirTool().execute({"path": "src"}, context)

    assert context.access.has_inspected_directory("src")
