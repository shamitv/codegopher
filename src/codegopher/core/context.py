"""Build provider context for an agent turn."""

from __future__ import annotations

from pathlib import Path

from codegopher.config.schema import ApprovalMode
from codegopher.core.conversation import Conversation
from codegopher.core.types import Message
from codegopher.tools.registry import ToolRegistry


def build_system_prompt(cwd: Path, registry: ToolRegistry, approval_mode: ApprovalMode) -> str:
    tool_names = ", ".join(tool.name for tool in registry.list())
    return (
        "You are CodeGopher, a headless coding agent.\n"
        f"Current working directory: {cwd}\n"
        f"Approval mode: {approval_mode.value}\n"
        f"Available tools: {tool_names}\n"
        "Safety rules: read files before editing existing files, inspect a parent directory "
        "before creating files, and obey approval results for write and shell tools."
    )


def build_messages(
    conversation: Conversation,
    *,
    cwd: Path,
    registry: ToolRegistry,
    approval_mode: ApprovalMode,
) -> list[Message]:
    return [
        {"role": "system", "content": build_system_prompt(cwd, registry, approval_mode)},
        *conversation.provider_messages(),
    ]

