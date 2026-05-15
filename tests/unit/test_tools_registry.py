from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from codegopher.core.errors import ToolExecutionError
from codegopher.tools.base import ToolContext, ToolResult
from codegopher.tools.registry import ToolRegistry


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
