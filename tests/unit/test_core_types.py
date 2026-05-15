from __future__ import annotations

from codegopher.core.types import Message, StreamEvent, ToolCall, ToolSchema


def test_core_type_imports_support_expected_shapes() -> None:
    message: Message = {"role": "user", "content": "hello"}
    tool_call: ToolCall = {"id": "call-1", "name": "read_file", "arguments": {"path": "x"}}
    schema: ToolSchema = {"type": "function", "function": {"name": "read_file"}}
    event: StreamEvent = {"type": "tool_call", "tool_call": tool_call}

    assert message["role"] == "user"
    assert schema["type"] == "function"
    assert event["type"] == "tool_call"

