from __future__ import annotations

from pathlib import Path

import pytest

from codegopher.tools.base import ToolContext
from codegopher.tools.fs.glob_search import GlobSearchTool


@pytest.mark.asyncio
async def test_glob_search_returns_matching_paths(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.py").write_text("", encoding="utf-8")
    (tmp_path / "src" / "b.txt").write_text("", encoding="utf-8")

    result = await GlobSearchTool().execute({"pattern": "src/*.py"}, ToolContext(cwd=tmp_path))

    assert result.content == "src/a.py"

