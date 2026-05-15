"""Glob path search."""

from __future__ import annotations

from typing import Any

from codegopher.tools.base import ToolContext, ToolResult
from codegopher.tools.fs.ignore import IgnoreMatcher


class GlobSearchTool:
    name = "glob_search"
    description = "Return paths matching a glob pattern relative to the project root."
    parameters: dict[str, Any] = {
        "type": "object",
        "properties": {"pattern": {"type": "string"}},
        "required": ["pattern"],
    }
    requires_approval = False

    async def execute(self, arguments: dict[str, Any], context: ToolContext) -> ToolResult:
        call_id = str(arguments.get("_tool_call_id", ""))
        pattern = str(arguments["pattern"])
        matcher = IgnoreMatcher.from_file(context.cwd)
        matches = sorted(
            path.relative_to(context.cwd).as_posix()
            for path in context.cwd.glob(pattern)
            if path.exists() and not matcher.matches(path, context.cwd)
        )
        return ToolResult(tool_call_id=call_id, content="\n".join(matches))
