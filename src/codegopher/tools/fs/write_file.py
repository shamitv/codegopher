"""Create or replace a text file."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from codegopher.core.errors import ToolExecutionError
from codegopher.tools.base import ToolContext, ToolResult


class WriteFileTool:
    name = "write_file"
    description = "Create or replace a UTF-8 text file after safety gates pass."
    parameters: dict[str, Any] = {
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "content": {"type": "string"},
        },
        "required": ["path", "content"],
    }
    requires_approval = True

    async def execute(self, arguments: dict[str, Any], context: ToolContext) -> ToolResult:
        call_id = str(arguments.get("_tool_call_id", ""))
        path = Path(str(arguments["path"]))
        target = path if path.is_absolute() else context.cwd / path
        try:
            if target.exists():
                context.access.require_prior_read(path)
            else:
                context.access.require_parent_inspection(path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(str(arguments["content"]), encoding="utf-8")
        except (OSError, ToolExecutionError) as exc:
            return ToolResult(tool_call_id=call_id, content=str(exc), is_error=True)
        context.access.record_file_read(path)
        return ToolResult(tool_call_id=call_id, content=f"Wrote {path.as_posix()}")

