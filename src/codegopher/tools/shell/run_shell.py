"""Run a shell command."""

from __future__ import annotations

import asyncio
from typing import Any

from codegopher.tools.base import ToolContext, ToolResult


class RunShellCommandTool:
    name = "run_shell_command"
    description = "Run a shell command with a timeout and capture stdout/stderr."
    parameters: dict[str, Any] = {
        "type": "object",
        "properties": {
            "command": {"type": "string"},
            "timeout_seconds": {"type": "integer", "minimum": 1},
        },
        "required": ["command"],
    }
    requires_approval = True

    async def execute(self, arguments: dict[str, Any], context: ToolContext) -> ToolResult:
        call_id = str(arguments.get("_tool_call_id", ""))
        command = str(arguments["command"])
        timeout = int(arguments.get("timeout_seconds", 30))
        process = await asyncio.create_subprocess_shell(
            command,
            cwd=context.cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(process.communicate(), timeout)
        except TimeoutError:
            process.kill()
            await process.communicate()
            return ToolResult(
                tool_call_id=call_id,
                content=f"Command timed out after {timeout} seconds",
                is_error=True,
            )

        stdout = stdout_bytes.decode("utf-8", errors="replace").rstrip()
        stderr = stderr_bytes.decode("utf-8", errors="replace").rstrip()
        content = f"exit_code: {process.returncode}\nstdout:\n{stdout}\nstderr:\n{stderr}"
        return ToolResult(
            tool_call_id=call_id,
            content=content,
            is_error=process.returncode != 0,
        )

