"""Conversation history helpers."""

from __future__ import annotations

from dataclasses import dataclass, field

from codegopher.core.types import Message, ToolCall
from codegopher.tools.base import ToolResult
from codegopher.utils.json import dumps_json


@dataclass
class Conversation:
    messages: list[Message] = field(default_factory=list)

    def append_user(self, content: str) -> None:
        self.messages.append({"role": "user", "content": content})

    def append_assistant(self, content: str | None, tool_calls: list[ToolCall] | None = None) -> None:
        message: Message = {"role": "assistant", "content": content}
        if tool_calls:
            message["tool_calls"] = [
                {
                    "id": tool_call["id"],
                    "type": "function",
                    "function": {
                        "name": tool_call["name"],
                        "arguments": dumps_json(tool_call["arguments"]),
                    },
                }
                for tool_call in tool_calls
            ]
        self.messages.append(message)

    def append_tool_result(self, result: ToolResult) -> None:
        self.messages.append(
            {
                "role": "tool",
                "tool_call_id": result.tool_call_id,
                "content": result.content,
            }
        )

    def provider_messages(self) -> list[Message]:
        return list(self.messages)
