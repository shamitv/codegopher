from __future__ import annotations

from codegopher.tools.base import ToolResult


def test_tool_result_serializes_to_dict() -> None:
    result = ToolResult(tool_call_id="call-1", content="ok")

    assert result.model_dump() == {
        "tool_call_id": "call-1",
        "content": "ok",
        "is_error": False,
    }

