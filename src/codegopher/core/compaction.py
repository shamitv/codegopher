"""Conversation compaction helpers."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from codegopher.core.types import CompactionReason, Message
from codegopher.utils.json import dumps_json

RECENT_USER_TURNS_TO_KEEP = 2


@dataclass(frozen=True)
class CompactionInput:
    older_messages: list[Message]
    recent_messages: list[Message]


def split_for_compaction(
    messages: list[Message],
    *,
    preserve_recent_user_turns: int = RECENT_USER_TURNS_TO_KEEP,
) -> CompactionInput:
    """Split provider-ready history into compactable older and preserved recent messages."""
    if preserve_recent_user_turns <= 0:
        return CompactionInput(older_messages=list(messages), recent_messages=[])

    user_indexes = [
        index for index, message in enumerate(messages) if message.get("role") == "user"
    ]
    if len(user_indexes) <= preserve_recent_user_turns:
        return CompactionInput(older_messages=[], recent_messages=list(messages))

    split_index = user_indexes[-preserve_recent_user_turns]
    return CompactionInput(
        older_messages=list(messages[:split_index]),
        recent_messages=list(messages[split_index:]),
    )


def build_compaction_prompt(
    messages: list[Message],
    *,
    cwd: Path,
    instructions: str | None = None,
    memories: Iterable[str] = (),
    skills: Iterable[str] = (),
    todo_items: Iterable[str] = (),
    preserve_recent_user_turns: int = RECENT_USER_TURNS_TO_KEEP,
) -> str:
    split = split_for_compaction(
        messages,
        preserve_recent_user_turns=preserve_recent_user_turns,
    )
    sections = [
        "Summarize the older CodeGopher session context so future turns retain the important state.",
        f"Current working directory: {cwd}",
        "Include user goals, decisions, files inspected, tool results, approvals or denials, and unresolved work.",
        "Do not invent facts. Keep the summary concise but specific.",
    ]
    if instructions:
        sections.append(f"User compaction instructions:\n{instructions}")
    sections.append("Older messages to summarize:\n" + _format_messages(split.older_messages))
    sections.append(
        "Recent messages to preserve verbatim outside the summary:\n"
        + _format_messages(split.recent_messages)
    )
    if todo := list(todo_items):
        sections.append("Active TODO state:\n" + "\n".join(f"- {item}" for item in todo))
    if memory_items := list(memories):
        sections.append("Selected memories:\n" + "\n".join(f"- {item}" for item in memory_items))
    if skill_items := list(skills):
        sections.append("Loaded skills:\n" + "\n".join(f"- {item}" for item in skill_items))
    sections.append("Return only the compaction summary text.")
    return "\n\n".join(sections)


def compacted_messages(
    messages: list[Message],
    *,
    summary: str,
    reason: CompactionReason,
    instructions: str | None = None,
    preserve_recent_user_turns: int = RECENT_USER_TURNS_TO_KEEP,
) -> list[Message]:
    split = split_for_compaction(
        messages,
        preserve_recent_user_turns=preserve_recent_user_turns,
    )
    content = f"Compaction summary ({reason}):\n{summary}"
    if instructions:
        content += f"\n\nInstructions used: {instructions}"
    return [{"role": "system", "content": content}, *split.recent_messages]


def compaction_id() -> str:
    return f"compact-{uuid4().hex[:12]}"


def _format_messages(messages: list[Message]) -> str:
    if not messages:
        return "(none)"
    return "\n".join(_format_message(index, message) for index, message in enumerate(messages, 1))


def _format_message(index: int, message: Message) -> str:
    role = message.get("role", "unknown")
    parts = [f"{index}. {role}:"]
    content = message.get("content")
    if content:
        parts.append(str(content))
    if tool_call_id := message.get("tool_call_id"):
        parts.append(f"tool_call_id={tool_call_id}")
    if tool_calls := message.get("tool_calls"):
        parts.append(f"tool_calls={dumps_json(tool_calls)}")
    if len(parts) == 1:
        parts.append("(no content)")
    return " ".join(parts)
