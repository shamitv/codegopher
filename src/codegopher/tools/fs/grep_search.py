"""Text grep search."""

from __future__ import annotations

import shutil
import subprocess
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
        rg_content = self._grep_with_rg(query, start, context.cwd)
        if rg_content is not None:
            return ToolResult(tool_call_id=call_id, content=rg_content)
        return ToolResult(tool_call_id=call_id, content=self._grep_with_python(query, start, context))

    def _grep_with_rg(self, query: str, start: Path, cwd: Path) -> str | None:
        if shutil.which("rg") is None:
            return None
        command = [
            "rg",
            "--line-number",
            "--no-heading",
            "--color",
            "never",
            "--path-separator",
            "/",
        ]
        ignore_file = cwd / ".codegopherignore"
        if ignore_file.exists():
            command.extend(["--ignore-file", str(ignore_file)])
        command.extend([query, start.as_posix()])
        completed = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        if completed.returncode == 0:
            return "\n".join(
                line[2:] if line.startswith("./") else line
                for line in completed.stdout.rstrip("\n").splitlines()
            )
        if completed.returncode == 1:
            return ""
        return None

    def _grep_with_python(self, query: str, start: Path, context: ToolContext) -> str:
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
        return "\n".join(matches)
