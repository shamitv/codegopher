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
        matches = []
        cwd = context.cwd.resolve()
        for path in context.cwd.glob(pattern):
            resolved = path.resolve()
            if not resolved.is_relative_to(cwd) or not resolved.exists():
                continue
            rel_path = resolved.relative_to(cwd).as_posix()
            if not matcher.matches(resolved, cwd):
                matches.append(rel_path)
        return ToolResult(tool_call_id=call_id, content="\n".join(sorted(matches)))
