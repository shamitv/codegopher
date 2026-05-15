"""Tool registry and schema export."""

from __future__ import annotations

import builtins

from codegopher.core.errors import ToolExecutionError
from codegopher.core.types import ToolSchema
from codegopher.tools.base import Tool


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        if tool.name in self._tools:
            raise ToolExecutionError(f"Duplicate tool registered: {tool.name}")
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        try:
            return self._tools[name]
        except KeyError as exc:
            raise ToolExecutionError(f"Unknown tool: {name}") from exc

    def list(self) -> builtins.list[Tool]:
        return builtins.list(self._tools.values())

    def schemas(self) -> builtins.list[ToolSchema]:
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                },
            }
            for tool in self.list()
        ]


def create_default_registry() -> ToolRegistry:
    from codegopher.tools.fs.edit_file import EditFileTool
    from codegopher.tools.fs.glob_search import GlobSearchTool
    from codegopher.tools.fs.grep_search import GrepSearchTool
    from codegopher.tools.fs.list_dir import ListDirTool
    from codegopher.tools.fs.read_file import ReadFileTool
    from codegopher.tools.fs.read_many_files import ReadManyFilesTool
    from codegopher.tools.fs.write_file import WriteFileTool
    from codegopher.tools.shell.run_shell import RunShellCommandTool

    registry = ToolRegistry()
    for tool in (
        ReadFileTool(),
        ReadManyFilesTool(),
        ListDirTool(),
        GlobSearchTool(),
        GrepSearchTool(),
        WriteFileTool(),
        EditFileTool(),
        RunShellCommandTool(),
    ):
        registry.register(tool)
    return registry
