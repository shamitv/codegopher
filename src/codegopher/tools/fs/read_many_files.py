"""Read multiple UTF-8 text files."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from codegopher.tools.base import ToolContext, ToolResult
from codegopher.tools.fs.ignore import IgnoreMatcher


class ReadManyFilesTool:
    name = "read_many_files"
    description = "Read a bounded set of UTF-8 files from explicit paths or glob patterns."
    parameters: dict[str, Any] = {
        "type": "object",
        "properties": {
            "paths": {"type": "array", "items": {"type": "string"}},
            "globs": {"type": "array", "items": {"type": "string"}},
            "max_files": {"type": "integer", "minimum": 1},
        },
    }
    requires_approval = False

    async def execute(self, arguments: dict[str, Any], context: ToolContext) -> ToolResult:
        call_id = str(arguments.get("_tool_call_id", ""))
        max_files = int(arguments.get("max_files", 20))
        matcher = IgnoreMatcher.from_file(context.cwd)
        candidates: list[Path] = []
        for raw_path in arguments.get("paths", []):
            path = Path(str(raw_path))
            candidates.append(path if path.is_absolute() else context.cwd / path)
        for pattern in arguments.get("globs", []):
            candidates.extend(context.cwd.glob(str(pattern)))

        unique = []
        seen: set[Path] = set()
        for path in sorted(candidates):
            if path in seen or not path.is_file() or matcher.matches(path, context.cwd):
                continue
            seen.add(path)
            unique.append(path)
            if len(unique) >= max_files:
                break

        sections: list[str] = []
        for path in unique:
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError) as exc:
                sections.append(f"## {path.relative_to(context.cwd).as_posix()}\nERROR: {exc}")
                continue
            context.access.record_file_read(path)
            sections.append(f"## {path.relative_to(context.cwd).as_posix()}\n{text.rstrip()}")
        return ToolResult(tool_call_id=call_id, content="\n\n".join(sections))

