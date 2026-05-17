"""Model-facing TODO update tool."""

from __future__ import annotations

from typing import Any

from codegopher.core.types import TodoStatus
from codegopher.tools.base import ToolContext, ToolResult


class UpdateTodoTool:
    name = "update_todo"
    description = "Update the current session TODO list."
    requires_approval = False
    parameters: dict[str, Any] = {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["add", "start", "done"]},
            "id": {"type": "string"},
            "text": {"type": "string"},
        },
        "required": ["action"],
        "additionalProperties": False,
    }

    async def execute(self, arguments: dict[str, Any], context: ToolContext) -> ToolResult:
        tool_call_id = str(arguments.get("_tool_call_id", ""))
        if not context.settings.todo.enabled:
            return ToolResult(
                tool_call_id=tool_call_id,
                content="TODO is disabled in settings",
                is_error=True,
            )
        if context.todo_state is None:
            return ToolResult(
                tool_call_id=tool_call_id,
                content="TODO state is unavailable",
                is_error=True,
            )

        action = arguments.get("action")
        if action == "add":
            text = str(arguments.get("text", "")).strip()
            if not text:
                return ToolResult(
                    tool_call_id=tool_call_id,
                    content="text is required for add",
                    is_error=True,
                )
            try:
                item = context.todo_state.add(text, source="tool")
            except ValueError as exc:
                return ToolResult(
                    tool_call_id=tool_call_id,
                    content=str(exc),
                    is_error=True,
                )
            return ToolResult(
                tool_call_id=tool_call_id,
                content=f"Added TODO {item.id}",
            )

        if action in {"start", "done"}:
            item_id = str(arguments.get("id", "")).strip()
            if not item_id:
                return ToolResult(
                    tool_call_id=tool_call_id,
                    content=f"id is required for {action}",
                    is_error=True,
                )
            status: TodoStatus = "in_progress" if action == "start" else "done"
            try:
                item = context.todo_state.set_status(item_id, status)
            except KeyError:
                return ToolResult(
                    tool_call_id=tool_call_id,
                    content=f"TODO not found: {item_id}",
                    is_error=True,
                )
            return ToolResult(
                tool_call_id=tool_call_id,
                content=f"Updated TODO {item.id} to {item.status}",
            )

        return ToolResult(
            tool_call_id=tool_call_id,
            content="action must be 'add', 'start', or 'done'",
            is_error=True,
        )
