"""Approval policy for tool execution."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable
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


def prompt_for_approval(
    request: ApprovalRequest,
    *,
    input_func: Callable[[str], str] = input,
    output_func: Callable[[str], None] = print,
) -> ApprovalResult:
    output_func(f"Tool requested: {request.tool_name}")
    output_func(f"Arguments: {request.arguments_preview}")
    answer = input_func("Approve? [y/N] ").strip().lower()
    if answer in {"y", "yes"}:
        return ApprovalResult(approved=True)
    return ApprovalResult(approved=False, reason="Denied by user")
