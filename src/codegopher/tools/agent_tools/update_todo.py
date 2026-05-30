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
            "action": {
                "type": "string",
                "enum": [
                    "add",
                    "update",
                    "start",
                    "block",
                    "unblock",
                    "done",
                    "cancel",
                ],
            },
            "id": {"type": "string"},
            "text": {"type": "string"},
            "reason": {"type": "string"},
            "related_files": {"type": "array", "items": {"type": "string"}},
            "evidence_refs": {"type": "array", "items": {"type": "string"}},
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
                item = context.todo_state.add(
                    text,
                    source="tool",
                    reason=_optional_str(arguments.get("reason")),
                    related_files=_string_list(arguments.get("related_files")),
                    evidence_refs=_string_list(arguments.get("evidence_refs")),
                )
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

        if action == "update":
            item_id = str(arguments.get("id", "")).strip()
            if not item_id:
                return ToolResult(
                    tool_call_id=tool_call_id,
                    content="id is required for update",
                    is_error=True,
                )
            if not any(
                key in arguments
                for key in ("text", "reason", "related_files", "evidence_refs")
            ):
                return ToolResult(
                    tool_call_id=tool_call_id,
                    content="update requires text, reason, related_files, or evidence_refs",
                    is_error=True,
                )
            try:
                item = context.todo_state.update(
                    item_id,
                    text=_optional_str(arguments.get("text")),
                    reason=_optional_str(arguments.get("reason")),
                    related_files=_string_list(arguments.get("related_files"))
                    if "related_files" in arguments
                    else None,
                    evidence_refs=_string_list(arguments.get("evidence_refs"))
                    if "evidence_refs" in arguments
                    else None,
                )
            except KeyError:
                return ToolResult(
                    tool_call_id=tool_call_id,
                    content=f"TODO not found: {item_id}",
                    is_error=True,
                )
            except ValueError as exc:
                return ToolResult(
                    tool_call_id=tool_call_id,
                    content=str(exc),
                    is_error=True,
                )
            return ToolResult(
                tool_call_id=tool_call_id,
                content=f"Updated TODO {item.id}",
            )

        if action in {"start", "block", "unblock", "done", "cancel"}:
            item_id = str(arguments.get("id", "")).strip()
            if not item_id:
                return ToolResult(
                    tool_call_id=tool_call_id,
                    content=f"id is required for {action}",
                    is_error=True,
                )
            status_by_action: dict[str, TodoStatus] = {
                "start": "in_progress",
                "block": "blocked",
                "unblock": "pending",
                "done": "done",
                "cancel": "cancelled",
            }
            status = status_by_action[action]
            try:
                item = context.todo_state.set_status(
                    item_id,
                    status,
                    reason=_optional_str(arguments.get("reason")),
                )
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
            content=(
                "action must be 'add', 'update', 'start', 'block', 'unblock', "
                "'done', or 'cancel'"
            ),
            is_error=True,
        )


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        return [str(value)]
    return [str(item) for item in value]
