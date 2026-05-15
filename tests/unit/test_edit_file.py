from __future__ import annotations

from pathlib import Path

import pytest

from codegopher.tools.base import ToolContext
from codegopher.tools.fs.edit_file import EditFileTool


@pytest.mark.asyncio
async def test_edit_file_replaces_exact_text(tmp_path: Path) -> None:
    (tmp_path / "example.txt").write_text("hello old\n", encoding="utf-8")
    context = ToolContext(cwd=tmp_path)
    context.access.record_file_read("example.txt")

    result = await EditFileTool().execute(
        {"path": "example.txt", "old": "old", "new": "new"},
        context,
    )

    assert result.is_error is False
    assert (tmp_path / "example.txt").read_text(encoding="utf-8") == "hello new\n"


@pytest.mark.asyncio
async def test_edit_file_requires_prior_read(tmp_path: Path) -> None:
    (tmp_path / "example.txt").write_text("hello old\n", encoding="utf-8")

    result = await EditFileTool().execute(
        {"path": "example.txt", "old": "old", "new": "new"},
        ToolContext(cwd=tmp_path),
    )

    assert result.is_error is True
    assert "must read it first" in result.content


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("content", "old", "new", "expected"),
    [
        ("alpha\n", "missing", "new", "not found"),
        ("same same\n", "same", "new", "matched 2 times"),
        ("alpha\n", "alpha", "alpha", "no-op"),
    ],
)
async def test_edit_file_rejects_ambiguous_or_noop_edits(
    tmp_path: Path,
    content: str,
    old: str,
    new: str,
    expected: str,
) -> None:
    (tmp_path / "example.txt").write_text(content, encoding="utf-8")
    context = ToolContext(cwd=tmp_path)
    context.access.record_file_read("example.txt")

    result = await EditFileTool().execute(
        {"path": "example.txt", "old": old, "new": new},
        context,
    )

    assert result.is_error is True
    assert expected in result.content


@pytest.mark.asyncio
async def test_edit_file_rejects_absolute_path_outside_cwd(tmp_path: Path) -> None:
    (tmp_path / "example.txt").write_text("hello\n", encoding="utf-8")
    context = ToolContext(cwd=tmp_path)
    context.access.record_file_read("example.txt")

    result = await EditFileTool().execute(
        {"path": "/etc/passwd", "old": "root", "new": "admin"},
        context,
    )

    assert result.is_error is True
    assert "outside project directory" in result.content


@pytest.mark.asyncio
async def test_edit_file_rejects_relative_path_escaping_cwd(tmp_path: Path) -> None:
    (tmp_path / "example.txt").write_text("hello\n", encoding="utf-8")
    context = ToolContext(cwd=tmp_path)
    context.access.record_file_read("../outside.txt")

    result = await EditFileTool().execute(
        {"path": "../outside.txt", "old": "old", "new": "new"},
        context,
    )

    assert result.is_error is True
    assert "outside project directory" in result.content
