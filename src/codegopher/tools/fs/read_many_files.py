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
        cwd = context.cwd.resolve()
        for path in sorted(candidates):
            resolved = path.resolve()
            if not resolved.is_relative_to(cwd):
                continue
            if resolved in seen or not resolved.is_file() or matcher.matches(resolved, cwd):
                continue
            seen.add(resolved)
            unique.append(resolved)
            if len(unique) >= max_files:
                break

        sections: list[str] = []
        for path in unique:
            try:
                rel_path = path.relative_to(cwd).as_posix()
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError) as exc:
                sections.append(f"## {rel_path}\nERROR: {exc}")
                continue
            context.access.record_file_read(path)
            sections.append(f"## {rel_path}\n{text.rstrip()}")
        return ToolResult(tool_call_id=call_id, content="\n\n".join(sections))
