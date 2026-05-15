from __future__ import annotations

import pytest

from codegopher.providers.mock import MockProvider


@pytest.mark.asyncio
async def test_mock_provider_streams_scripted_events() -> None:
    provider = MockProvider([[{"type": "text_delta", "content": "hello"}, {"type": "done"}]])

    events = [
        event
        async for event in provider.stream([], [], model="test", temperature=0, max_output_tokens=1)
    ]

    assert events == [{"type": "text_delta", "content": "hello"}, {"type": "done"}]


@pytest.mark.asyncio
async def test_mock_provider_records_message_calls() -> None:
    provider = MockProvider([[{"type": "text_delta", "content": "ok"}, {"type": "done"}]])

    events = [
        event
        async for event in provider.stream(
            [{"role": "user", "content": "hello"}],
            [],
            model="test",
            temperature=0,
            max_output_tokens=1,
        )
    ]

    assert events[0] == {"type": "text_delta", "content": "ok"}
    assert provider.calls == [[{"role": "user", "content": "hello"}]]


@pytest.mark.asyncio
async def test_mock_provider_streams_tool_call_events() -> None:
    tool_event = {
        "type": "tool_call",
        "tool_call": {"id": "call-1", "name": "read_file", "arguments": {"path": "README.md"}},
    }
    provider = MockProvider([[tool_event, {"type": "done"}]])

    events = [
        event
        async for event in provider.stream([], [], model="test", temperature=0, max_output_tokens=1)
    ]

    assert events[0] == tool_event
