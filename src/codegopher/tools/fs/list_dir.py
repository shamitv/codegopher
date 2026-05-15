"""List a directory."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from codegopher.tools.base import ToolContext, ToolResult


class ListDirTool:
    name = "list_dir"
    description = "List a directory's immediate children."
    parameters: dict[str, Any] = {
        "type": "object",
        "properties": {"path": {"type": "string"}},
        "required": ["path"],
    }
    requires_approval = False

    async def execute(self, arguments: dict[str, Any], context: ToolContext) -> ToolResult:
        call_id = str(arguments.get("_tool_call_id", ""))
        path = Path(str(arguments["path"]))
        target = path if path.is_absolute() else context.cwd / path
        try:
            entries = sorted(target.iterdir(), key=lambda item: item.name.lower())
        except OSError as exc:
            return ToolResult(tool_call_id=call_id, content=str(exc), is_error=True)

        context.access.record_directory_inspection(path)
        rendered = [f"{entry.name}/" if entry.is_dir() else entry.name for entry in entries]
        return ToolResult(tool_call_id=call_id, content="\n".join(rendered))

