"""Build provider context for an agent turn."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from codegopher.config.schema import ApprovalMode
from codegopher.core.conversation import Conversation
from codegopher.core.types import Message
from codegopher.tools.registry import ToolRegistry


def build_system_prompt(
    cwd: Path,
    registry: ToolRegistry,
    approval_mode: ApprovalMode,
    *,
    memories: Iterable[str] = (),
    episode_items: Iterable[str] = (),
    skills: Iterable[str] = (),
    todo_items: Iterable[str] = (),
    mission_items: Iterable[str] = (),
) -> str:
    tool_names = ", ".join(tool.name for tool in registry.list())
    prompt = (
        "You are CodeGopher, a headless coding agent.\n"
        f"Current working directory: {cwd}\n"
        f"Approval mode: {approval_mode.value}\n"
        f"Available tools: {tool_names}\n"
        "Safety rules: read files before editing existing files, inspect a parent directory "
        "before creating files, and obey approval results for write and shell tools."
    )
    memory_items = list(memories)
    if memory_items:
        prompt += "\nSelected memories:\n" + "\n".join(
            f"- {memory}" for memory in memory_items
        )
    episode_context = list(episode_items)
    if episode_context:
        prompt += (
            "\nRuntime episode memory:\n"
            "These are task-local observations from this active session, not persistent memory. "
            "Use them to avoid losing inspected evidence and unresolved pivots; do not save them "
            "to long-term memory unless the user explicitly asks.\n"
            + "\n".join(f"- {item}" for item in episode_context)
        )
    skill_items = list(skills)
    if skill_items:
        prompt += "\nLoaded skills:\n" + "\n\n".join(skill_items)
    active_todo_items = list(todo_items)
    if active_todo_items:
        prompt += "\nActive TODOs:\n" + "\n".join(
            f"- {item}" for item in active_todo_items
        )
    active_mission_items = list(mission_items)
    if active_mission_items:
        prompt += "\nActive mission contract:\n" + "\n".join(
            f"- {item}" for item in active_mission_items
        )
    return prompt


def build_messages(
    conversation: Conversation,
    *,
    cwd: Path,
    registry: ToolRegistry,
    approval_mode: ApprovalMode,
    memories: Iterable[str] = (),
    episode_items: Iterable[str] = (),
    skills: Iterable[str] = (),
    todo_items: Iterable[str] = (),
    mission_items: Iterable[str] = (),
) -> list[Message]:
    return [
        {
            "role": "system",
            "content": build_system_prompt(
                cwd,
                registry,
                approval_mode,
                memories=memories,
                episode_items=episode_items,
                skills=skills,
                todo_items=todo_items,
                mission_items=mission_items,
            ),
        },
        *conversation.provider_messages(),
    ]
