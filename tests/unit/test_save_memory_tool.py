from __future__ import annotations

from pathlib import Path

import pytest

from codegopher.config.schema import Settings
from codegopher.memory import MemoryStore
from codegopher.tools.agent_tools import SaveMemoryTool
from codegopher.tools.base import ToolContext


@pytest.mark.asyncio
async def test_save_memory_tool_saves_project_memory(tmp_path: Path) -> None:
    store = MemoryStore(data_home=tmp_path / "data")
    context = ToolContext(cwd=tmp_path, memory_store=store)
    tool = SaveMemoryTool()

    result = await tool.execute(
        {"scope": "project", "content": "Use pytest", "_tool_call_id": "call-1"},
        context,
    )

    entries = store.list_entries("project", cwd=tmp_path)
    assert result.is_error is False
    assert result.tool_call_id == "call-1"
    assert result.content == f"Saved project memory {entries[0].id}"
    assert entries[0].content == "Use pytest"
    assert entries[0].source == "tool"


@pytest.mark.asyncio
async def test_save_memory_tool_saves_session_memory_when_session_id_exists(
    tmp_path: Path,
) -> None:
    store = MemoryStore(data_home=tmp_path / "data")
    context = ToolContext(cwd=tmp_path, memory_store=store, session_id="session-1")

    result = await SaveMemoryTool().execute(
        {"scope": "session", "content": "Current task"},
        context,
    )

    assert result.is_error is False
    assert store.list_entries("session", session_id="session-1")[0].content == "Current task"


@pytest.mark.asyncio
async def test_save_memory_tool_rejects_session_memory_without_session_id(
    tmp_path: Path,
) -> None:
    context = ToolContext(cwd=tmp_path, memory_store=MemoryStore(data_home=tmp_path / "data"))

    result = await SaveMemoryTool().execute(
        {"scope": "session", "content": "Current task"},
        context,
    )

    assert result.is_error is True
    assert "requires a session id" in result.content


@pytest.mark.asyncio
async def test_save_memory_tool_rejects_invalid_scope_and_content(tmp_path: Path) -> None:
    context = ToolContext(cwd=tmp_path, memory_store=MemoryStore(data_home=tmp_path / "data"))

    bad_scope = await SaveMemoryTool().execute({"scope": "global", "content": "x"}, context)
    empty = await SaveMemoryTool().execute({"scope": "project", "content": " "}, context)

    assert bad_scope.is_error is True
    assert "scope" in bad_scope.content
    assert empty.is_error is True
    assert "content is required" in empty.content


@pytest.mark.asyncio
async def test_save_memory_tool_respects_memory_settings(tmp_path: Path) -> None:
    settings = Settings.model_validate({"memory": {"enabled": False}})
    context = ToolContext(
        cwd=tmp_path,
        settings=settings,
        memory_store=MemoryStore(data_home=tmp_path / "data"),
    )

    result = await SaveMemoryTool().execute(
        {"scope": "project", "content": "Use pytest"},
        context,
    )

    assert result.is_error is True
    assert "disabled" in result.content


def test_save_memory_tool_requires_approval() -> None:
    assert SaveMemoryTool().requires_approval is True
