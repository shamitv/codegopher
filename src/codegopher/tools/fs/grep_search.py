"""Text grep search."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from codegopher.tools.base import ToolContext, ToolResult
from codegopher.tools.fs.ignore import IgnoreMatcher


class GrepSearchTool:
    name = "grep_search"
    description = "Search UTF-8 text files for a literal query."
    parameters: dict[str, Any] = {
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "path": {"type": "string"},
        },
        "required": ["query"],
    }
    requires_approval = False

    async def execute(self, arguments: dict[str, Any], context: ToolContext) -> ToolResult:
        call_id = str(arguments.get("_tool_call_id", ""))
        query = str(arguments["query"])
        start = Path(str(arguments.get("path", ".")))
        root = start if start.is_absolute() else context.cwd / start
        matcher = IgnoreMatcher.from_file(context.cwd)
        matches: list[str] = []
        for path in sorted(root.rglob("*")):
            if not path.is_file() or matcher.matches(path, context.cwd):
                continue
            try:
                lines = path.read_text(encoding="utf-8").splitlines()
            except UnicodeDecodeError:
                continue
            for number, line in enumerate(lines, start=1):
                if query in line:
                    rel = path.relative_to(context.cwd).as_posix()
                    matches.append(f"{rel}:{number}:{line}")
        return ToolResult(tool_call_id=call_id, content="\n".join(matches))

