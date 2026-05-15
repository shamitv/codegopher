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


@pytest.mark.asyncio
async def test_write_file_rejects_new_file_without_parent_inspection(tmp_path: Path) -> None:
    result = await WriteFileTool().execute(
        {"path": "created.txt", "content": "hello"},
        ToolContext(cwd=tmp_path),
    )

    assert result.is_error is True
    assert "list_dir must inspect parent directory" in result.content
    assert not (tmp_path / "created.txt").exists()


@pytest.mark.asyncio
async def test_write_file_replaces_existing_file_after_prior_read(tmp_path: Path) -> None:
    (tmp_path / "existing.txt").write_text("old", encoding="utf-8")
    context = ToolContext(cwd=tmp_path)
    context.access.record_file_read("existing.txt")

    result = await WriteFileTool().execute({"path": "existing.txt", "content": "new"}, context)

    assert result.is_error is False
    assert (tmp_path / "existing.txt").read_text(encoding="utf-8") == "new"


@pytest.mark.asyncio
async def test_write_file_rejects_replacement_without_prior_read(tmp_path: Path) -> None:
    (tmp_path / "existing.txt").write_text("old", encoding="utf-8")

    result = await WriteFileTool().execute(
        {"path": "existing.txt", "content": "new"},
        ToolContext(cwd=tmp_path),
    )

    assert result.is_error is True
    assert "must read it first" in result.content
    assert (tmp_path / "existing.txt").read_text(encoding="utf-8") == "old"
