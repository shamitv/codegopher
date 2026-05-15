"""Approval policy for tool execution."""

from __future__ import annotations

from collections.abc import Callable
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


def resolve_approval(
    mode: ApprovalMode,
    tool: ApprovableTool,
    request: ApprovalRequest,
    *,
    stdin_is_tty: bool,
) -> ApprovalResult:
    if not should_prompt(mode, tool):
        return ApprovalResult(approved=True)
    if not stdin_is_tty:
        return ApprovalResult(approved=False, reason="Approval required but stdin is not a TTY")
    return prompt_for_approval(request)
