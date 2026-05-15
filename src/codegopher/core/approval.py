"""Approval policy for tool execution."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from codegopher.config.schema import ApprovalMode


class ApprovableTool(Protocol):
    requires_approval: bool


def should_prompt(mode: ApprovalMode, tool: ApprovableTool) -> bool:
    return mode == ApprovalMode.auto or (
        mode == ApprovalMode.review and tool.requires_approval
    )


@dataclass(frozen=True)
class ApprovalRequest:
    tool_name: str
    arguments_preview: str


@dataclass(frozen=True)
class ApprovalResult:
    approved: bool
    reason: str | None = None

