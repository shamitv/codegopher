from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

import codegopher.tools.fs.grep_search as grep_module
from codegopher.tools.base import ToolContext
from codegopher.tools.fs.grep_search import GrepSearchTool


@pytest.mark.asyncio
async def test_grep_search_finds_literal_text(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.txt").write_text("needle\nother\n", encoding="utf-8")

    result = await GrepSearchTool().execute({"query": "needle"}, ToolContext(cwd=tmp_path))

    assert result.content == "src/a.txt:1:needle"


@pytest.mark.asyncio
async def test_grep_search_can_use_rg_fast_path(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(grep_module.shutil, "which", lambda _name: "rg")
    monkeypatch.setattr(
        grep_module.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout="src/a.txt:1:needle\n"),
    )

    result = await GrepSearchTool().execute({"query": "needle"}, ToolContext(cwd=tmp_path))

    assert result.content == "src/a.txt:1:needle"
