from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from codegopher.core.errors import ToolExecutionError
from codegopher.tools.base import ToolContext, ToolResult
from codegopher.tools.registry import ToolRegistry, create_default_registry


@dataclass
class FakeTool:
    name: str = "fake"
    description: str = "Fake tool"
    parameters: dict[str, Any] | None = None
    requires_approval: bool = False

    async def execute(self, arguments: dict[str, Any], context: ToolContext) -> ToolResult:
        return ToolResult(tool_call_id="", content="")


def test_tool_registry_registers_and_gets_tool() -> None:
    registry = ToolRegistry()
    tool = FakeTool(parameters={"type": "object"})

    registry.register(tool)

    assert registry.get("fake") is tool


def test_tool_registry_rejects_duplicate_names() -> None:
    registry = ToolRegistry()
    registry.register(FakeTool(parameters={"type": "object"}))

    with pytest.raises(ToolExecutionError, match="Duplicate tool"):
        registry.register(FakeTool(parameters={"type": "object"}))


def test_tool_registry_exports_tool_schemas() -> None:
    registry = ToolRegistry()
    registry.register(
        FakeTool(parameters={"type": "object", "properties": {"path": {"type": "string"}}})
    )

    assert registry.schemas() == [
        {
            "type": "function",
            "function": {
                "name": "fake",
                "description": "Fake tool",
                "parameters": {"type": "object", "properties": {"path": {"type": "string"}}},
            },
        }
    ]


def test_default_registry_contains_read_only_file_tools() -> None:
    registry = create_default_registry()

    assert [tool.name for tool in registry.list()] == [
        "read_file",
        "read_many_files",
        "list_dir",
        "glob_search",
        "grep_search",
        "write_file",
        "edit_file",
        "run_shell_command",
        "save_memory",
    ]
