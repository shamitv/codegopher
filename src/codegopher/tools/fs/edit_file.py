"""Apply an exact text replacement to a file."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from codegopher.core.errors import ToolExecutionError
from codegopher.tools.base import ToolContext, ToolResult


class EditFileTool:
    name = "edit_file"
    description = "Replace one exact text occurrence in an existing UTF-8 file."
    parameters: dict[str, Any] = {
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "old": {"type": "string"},
            "new": {"type": "string"},
        },
        "required": ["path", "old", "new"],
    }
    requires_approval = True

    async def execute(self, arguments: dict[str, Any], context: ToolContext) -> ToolResult:
        call_id = str(arguments.get("_tool_call_id", ""))
        path = Path(str(arguments["path"]))
        target = path if path.is_absolute() else context.cwd / path
        old = str(arguments["old"])
        new = str(arguments["new"])
        try:
            context.access.require_prior_read(path)
            text = target.read_text(encoding="utf-8")
            count = text.count(old)
            if count == 0:
                return ToolResult(tool_call_id=call_id, content="Text to replace was not found", is_error=True)
            if count > 1:
                return ToolResult(
                    tool_call_id=call_id,
                    content=f"Text to replace matched {count} times; expected exactly one",
                    is_error=True,
                )
            if old == new:
                return ToolResult(tool_call_id=call_id, content="Edit is a no-op", is_error=True)
            target.write_text(text.replace(old, new, 1), encoding="utf-8")
        except (OSError, UnicodeDecodeError, ToolExecutionError) as exc:
            return ToolResult(tool_call_id=call_id, content=str(exc), is_error=True)
        context.access.record_file_read(path)
        return ToolResult(tool_call_id=call_id, content=f"Edited {path.as_posix()}")

