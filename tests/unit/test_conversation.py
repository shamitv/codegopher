from __future__ import annotations

from codegopher.core.conversation import Conversation
from codegopher.tools.base import ToolResult


def test_conversation_appends_user_assistant_and_tool_result() -> None:
    conversation = Conversation()

    conversation.append_user("hello")
    conversation.append_assistant("hi")
    conversation.append_tool_result(ToolResult(tool_call_id="call-1", content="ok"))

    assert conversation.messages == [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "hi"},
        {"role": "tool", "tool_call_id": "call-1", "content": "ok"},
    ]


def test_conversation_converts_tool_calls_for_provider_messages() -> None:
    conversation = Conversation()
    conversation.append_assistant(
        None,
        [{"id": "call-1", "name": "read_file", "arguments": {"path": "README.md"}}],
    )

    assert conversation.provider_messages()[0]["tool_calls"] == [
        {
            "id": "call-1",
            "type": "function",
            "function": {"name": "read_file", "arguments": {"path": "README.md"}},
        }
    ]
