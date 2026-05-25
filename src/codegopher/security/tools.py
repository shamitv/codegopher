"""Security-audit-specific tools."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from codegopher.security.report import DEFAULT_CHAINED_VULNERABILITY_REPORT
from codegopher.tools.base import ToolContext, ToolResult


class WriteChainedVulnerabilityReportTool:
    name = "write_chained_vulnerability_report"
    description = (
        "Write the chained vulnerability audit report to "
        "docs/security/CHAINED_VULNERABILITIES_REVIEW.md."
    )
    parameters: dict[str, Any] = {
        "type": "object",
        "properties": {
            "content": {"type": "string"},
        },
        "required": ["content"],
        "additionalProperties": False,
    }
    requires_approval = True

    async def execute(self, arguments: dict[str, Any], context: ToolContext) -> ToolResult:
        call_id = str(arguments.get("_tool_call_id", ""))
        target = context.cwd / DEFAULT_CHAINED_VULNERABILITY_REPORT
        try:
            resolved = target.resolve()
            if not resolved.is_relative_to(context.cwd.resolve()):
                return ToolResult(
                    tool_call_id=call_id,
                    content="Report path resolves outside project directory",
                    is_error=True,
                )
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(str(arguments["content"]), encoding="utf-8")
            context.access.record_file_read(Path(DEFAULT_CHAINED_VULNERABILITY_REPORT))
        except OSError as exc:
            return ToolResult(tool_call_id=call_id, content=str(exc), is_error=True)
        return ToolResult(
            tool_call_id=call_id,
            content=f"Wrote {DEFAULT_CHAINED_VULNERABILITY_REPORT.as_posix()}",
        )
