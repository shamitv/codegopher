"""Static security audit tool policy."""

from __future__ import annotations

from codegopher.core.errors import ToolExecutionError
from codegopher.security.tools import WriteChainedVulnerabilityReportTool
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


def create_static_audit_registry(source: ToolRegistry) -> ToolRegistry:
    registry = ToolRegistry()
    for tool_name in STATIC_AUDIT_ALLOWED_TOOL_NAMES:
        try:
            registry.register(source.get(tool_name))
        except ToolExecutionError:
            continue
    registry.register(WriteChainedVulnerabilityReportTool())
    return registry


def uses_chained_vulnerability_skill(loaded_skill_ids: tuple[str, ...]) -> bool:
    return CHAINED_VULNERABILITY_SKILL_ID in loaded_skill_ids
