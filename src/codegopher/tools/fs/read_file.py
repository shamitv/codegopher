"""Read a UTF-8 text file."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from codegopher.tools.base import ToolContext, ToolResult


class ReadFileTool:
    name = "read_file"
    description = "Read a UTF-8 text file with optional 1-based inclusive line bounds."
    parameters: dict[str, Any] = {
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "start_line": {"type": "integer", "minimum": 1},
            "end_line": {"type": "integer", "minimum": 1},
        },
        "required": ["path"],
    }
    requires_approval = False

    async def execute(self, arguments: dict[str, Any], context: ToolContext) -> ToolResult:
        call_id = str(arguments.get("_tool_call_id", ""))
        path = Path(str(arguments["path"]))
        target = path if path.is_absolute() else context.cwd / path
        try:
            resolved = target.resolve()
            if not resolved.is_relative_to(context.cwd.resolve()):
                return ToolResult(
                    tool_call_id=call_id,
                    content=f"Path {path.as_posix()} resolves outside project directory",
                    is_error=True,
                )
            text = target.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            return ToolResult(tool_call_id=call_id, content=str(exc), is_error=True)

        lines = text.splitlines()
        start = int(arguments["start_line"]) if "start_line" in arguments else 1
        end = int(arguments["end_line"]) if "end_line" in arguments else len(lines)
        if start < 1 or end < start:
            return ToolResult(tool_call_id=call_id, content="Invalid line bounds", is_error=True)
        selected = lines[start - 1 : end]
        context.access.record_file_read(path)
        return ToolResult(tool_call_id=call_id, content="\n".join(selected))

