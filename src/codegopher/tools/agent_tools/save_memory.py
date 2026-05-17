"""Model-facing memory save tool."""

from __future__ import annotations

from typing import Any

from codegopher.memory import MemoryStore
from codegopher.tools.base import ToolContext, ToolResult


class SaveMemoryTool:
    name = "save_memory"
    description = "Persist explicit user-approved memory for this session or project."
    requires_approval = True
    parameters: dict[str, Any] = {
        "type": "object",
        "properties": {
            "scope": {"type": "string", "enum": ["session", "project"]},
            "content": {"type": "string"},
        },
        "required": ["scope", "content"],
        "additionalProperties": False,
    }

    async def execute(self, arguments: dict[str, Any], context: ToolContext) -> ToolResult:
        tool_call_id = str(arguments.get("_tool_call_id", ""))
        scope = arguments.get("scope")
        content = str(arguments.get("content", "")).strip()
        settings = context.settings
        if not settings.memory.enabled:
            return ToolResult(
                tool_call_id=tool_call_id,
                content="Memory is disabled in settings",
                is_error=True,
            )
        if scope not in {"session", "project"}:
            return ToolResult(
                tool_call_id=tool_call_id,
                content="scope must be 'session' or 'project'",
                is_error=True,
            )
        if not content:
            return ToolResult(
                tool_call_id=tool_call_id,
                content="content is required",
                is_error=True,
            )
        if scope == "session" and not settings.memory.session_enabled:
            return ToolResult(
                tool_call_id=tool_call_id,
                content="Session memory is disabled in settings",
                is_error=True,
            )
        if scope == "project" and not settings.memory.project_enabled:
            return ToolResult(
                tool_call_id=tool_call_id,
                content="Project memory is disabled in settings",
                is_error=True,
            )
        if scope == "session" and not context.session_id:
            return ToolResult(
                tool_call_id=tool_call_id,
                content="Session memory requires a session id",
                is_error=True,
            )
        store = context.memory_store or MemoryStore.default()
        entry = store.add_entry(
            scope,
            content=content,
            source="tool",
            session_id=context.session_id if scope == "session" else None,
            cwd=context.cwd if scope == "project" else None,
            max_entries=settings.memory.max_entries_per_scope,
            max_entry_chars=settings.memory.max_entry_chars,
        )
        return ToolResult(
            tool_call_id=tool_call_id,
            content=f"Saved {scope} memory {entry.id}",
        )
