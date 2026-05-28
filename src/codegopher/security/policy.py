"""Static security audit tool policy."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from codegopher.core.errors import ToolExecutionError
from codegopher.security.tools import WriteChainedVulnerabilityReportTool
from codegopher.tools.base import Tool, ToolContext, ToolResult
from codegopher.tools.registry import ToolRegistry

CHAINED_VULNERABILITY_SKILL_ID = "chained-vulnerability-static-audit"

STATIC_AUDIT_ALLOWED_TOOL_NAMES = (
    "read_file",
    "read_many_files",
    "list_dir",
    "glob_search",
    "grep_search",
    "update_todo",
)

STATIC_AUDIT_BLOCKED_NAMES = {
    ".vulns",
    "vulns.json",
    "scenarios.md",
    "impl_plan.md",
}
STATIC_AUDIT_BLOCKED_QUERY_TERMS = (
    "chain link",
    "decoy",
    "ground truth",
    "owasp",
    "cwe",
    "vulnerability",
    "vulnerabilities",
    "vulnerable",
)


def create_static_audit_registry(source: ToolRegistry) -> ToolRegistry:
    registry = ToolRegistry()
    for tool_name in STATIC_AUDIT_ALLOWED_TOOL_NAMES:
        try:
            registry.register(StaticAuditGuardTool(source.get(tool_name)))
        except ToolExecutionError:
            continue
    registry.register(WriteChainedVulnerabilityReportTool())
    return registry


def uses_chained_vulnerability_skill(loaded_skill_ids: tuple[str, ...]) -> bool:
    return CHAINED_VULNERABILITY_SKILL_ID in loaded_skill_ids


@dataclass
class StaticAuditGuardTool:
    """Policy wrapper for read/search tools exposed during chained audits."""

    delegate: Tool
    name: str = field(init=False)
    description: str = field(init=False)
    parameters: dict[str, Any] = field(init=False)
    requires_approval: bool = field(init=False)

    def __post_init__(self) -> None:
        self.name = self.delegate.name
        self.description = self.delegate.description
        self.parameters = self.delegate.parameters
        self.requires_approval = self.delegate.requires_approval

    async def execute(self, arguments: dict[str, Any], context: ToolContext) -> ToolResult:
        call_id = str(arguments.get("_tool_call_id", ""))
        violation = _static_audit_violation(self.name, arguments)
        if violation is not None:
            return ToolResult(
                tool_call_id=call_id,
                content=violation,
                is_error=True,
            )
        return await self.delegate.execute(arguments, context)


def _static_audit_violation(tool_name: str, arguments: dict[str, Any]) -> str | None:
    path_values = _argument_path_values(arguments)
    for raw_path in path_values:
        violation = _path_violation(raw_path)
        if violation is not None:
            return violation
    if tool_name == "grep_search":
        query = str(arguments.get("query", ""))
        normalized = query.lower()
        for term in STATIC_AUDIT_BLOCKED_QUERY_TERMS:
            if term in normalized:
                return (
                    "Static audit search denied: query appears to target evaluator "
                    "metadata or answer-key terminology"
                )
    return None


def _argument_path_values(arguments: dict[str, Any]) -> list[str]:
    values: list[str] = []
    for key in ("path", "pattern"):
        value = arguments.get(key)
        if value is not None:
            values.append(str(value))
    for key in ("paths", "globs"):
        value = arguments.get(key)
        if isinstance(value, list):
            values.extend(str(item) for item in value)
    return values


def _path_violation(raw_path: str) -> str | None:
    path = Path(raw_path)
    parts = [part for part in path.parts if part not in {"", "."}]
    if ".." in parts:
        return "Static audit path denied: parent-directory traversal is not allowed"
    for part in parts:
        lowered = part.lower()
        if lowered in STATIC_AUDIT_BLOCKED_NAMES:
            return "Static audit path denied: evaluator metadata is not allowed"
        if lowered.startswith("."):
            return "Static audit path denied: dotfiles and hidden paths are not allowed"
    return None
