from __future__ import annotations

import pytest

from codegopher.core.errors import ProviderError
from codegopher.providers.openai_responses import (
    OpenAIResponsesProvider,
    build_responses_request_preview,
)


class AsyncStream:
    def __init__(self, items: list[object] | None = None) -> None:
        self.items = list(items or [])

    def __aiter__(self) -> AsyncStream:
        return self

    async def __anext__(self) -> object:
        if not self.items:
            raise StopAsyncIteration
        return self.items.pop(0)


class FakeResponses:
    def __init__(self, stream: AsyncStream | None = None, error: Exception | None = None) -> None:
        self.kwargs = {}
        self.stream = stream or AsyncStream()
        self.error = error

    async def create(self, **kwargs):
        self.kwargs = kwargs
        if self.error:
            raise self.error
        return self.stream


class FakeClient:
    def __init__(self, stream: AsyncStream | None = None, error: Exception | None = None) -> None:
        self.responses = FakeResponses(stream, error)


def test_openai_responses_provider_resolves_api_key() -> None:
    provider = OpenAIResponsesProvider(environ={"OPENAI_API_KEY": "sk-test"}, client=object())

    assert provider.api_key == "sk-test"
    assert provider.api_key_env == "OPENAI_API_KEY"


def test_openai_responses_provider_reports_missing_api_key() -> None:
    with pytest.raises(ProviderError, match="OPENAI_API_KEY"):
        OpenAIResponsesProvider(environ={}, client=object())


@pytest.mark.asyncio
async def test_openai_responses_provider_builds_stateless_request() -> None:
    client = FakeClient()
    provider = OpenAIResponsesProvider(environ={"OPENAI_API_KEY": "sk-test"}, client=client)

    events = [
        event
        async for event in provider.stream(
            [
                {"role": "system", "content": "You are useful."},
                {"role": "user", "content": "hello"},
            ],
            [
                {
                    "type": "function",
                    "function": {
                        "name": "read_file",
                        "description": "Read a file",
                        "parameters": {"type": "object", "properties": {}},
                    },
                }
            ],
            model="gpt-test",
            temperature=0.2,
            max_output_tokens=128,
        )
    ]

    assert events == [{"type": "done", "finish_reason": None}]
    assert client.responses.kwargs["model"] == "gpt-test"
    assert client.responses.kwargs["instructions"] == "You are useful."
    assert client.responses.kwargs["input"] == [{"role": "user", "content": "hello"}]
    assert client.responses.kwargs["stream"] is True
    assert client.responses.kwargs["store"] is False
    assert client.responses.kwargs["max_output_tokens"] == 128
    assert client.responses.kwargs["temperature"] == 0.2
    assert client.responses.kwargs["tools"] == [
        {
            "type": "function",
            "name": "read_file",
            "description": "Read a file",
            "parameters": {"type": "object", "properties": {}},
        }
    ]
    assert client.responses.kwargs["tool_choice"] == "auto"


def test_openai_responses_input_replays_local_response_items_and_tool_outputs() -> None:
    request = build_responses_request_preview(
        [
            {"role": "system", "content": "system one"},
            {"role": "system", "content": "system two"},
            {"role": "user", "content": "find it"},
            {
                "role": "assistant",
                "content": None,
                "response_items": [
                    {
                        "type": "function_call",
                        "id": "fc-1",
                        "call_id": "call-1",
                        "name": "search",
                        "arguments": '{"query":"docs"}',
                    }
                ],
            },
            {"role": "tool", "tool_call_id": "call-1", "content": "result"},
            {"role": "assistant", "content": "done"},
        ],
        [],
        model="gpt-test",
        temperature=1.0,
        max_output_tokens=64,
    )

    assert request["instructions"] == "system one\n\nsystem two"
    assert request["input"] == [
        {"role": "user", "content": "find it"},
        {
            "type": "function_call",
            "id": "fc-1",
            "call_id": "call-1",
            "name": "search",
            "arguments": '{"query":"docs"}',
        },
        {"type": "function_call_output", "call_id": "call-1", "output": "result"},
        {"role": "assistant", "content": "done"},
    ]


def test_openai_responses_input_synthesizes_chat_tool_history_without_metadata() -> None:
    request = build_responses_request_preview(
        [
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call-1",
                        "type": "function",
                        "function": {"name": "read_file", "arguments": '{"path":"README.md"}'},
                    }
                ],
            }
        ],
        [],
        model="gpt-test",
        temperature=1.0,
        max_output_tokens=64,
    )

    assert request["input"] == [
        {
            "type": "function_call",
            "call_id": "call-1",
            "name": "read_file",
            "arguments": '{"path":"README.md"}',
        }
    ]


@pytest.mark.asyncio
async def test_openai_responses_provider_parses_text_deltas() -> None:
    client = FakeClient(
        AsyncStream(
            [
                {"type": "response.output_text.delta", "delta": "hel"},
                {"type": "response.output_text.delta", "delta": "lo"},
                {"type": "response.completed", "finish_reason": "stop"},
            ]
        )
    )
    provider = OpenAIResponsesProvider(environ={"OPENAI_API_KEY": "sk-test"}, client=client)

    events = [event async for event in provider.stream([], [], model="m", temperature=0, max_output_tokens=1)]

    assert events == [
        {"type": "text_delta", "content": "hel"},
        {"type": "text_delta", "content": "lo"},
        {"type": "done", "finish_reason": "stop"},
    ]


@pytest.mark.asyncio
async def test_openai_responses_provider_buffers_function_arguments_and_preserves_item() -> None:
    client = FakeClient(
        AsyncStream(
            [
                {"type": "response.function_call_arguments.delta", "item_id": "fc-1", "delta": "{"},
                {
                    "type": "response.function_call_arguments.done",
                    "item_id": "fc-1",
                    "arguments": '{"path":"README.md"}',
                },
                {
                    "type": "response.output_item.done",
                    "item": {
                        "type": "function_call",
                        "id": "fc-1",
                        "call_id": "call-1",
                        "name": "read_file",
                    },
                },
            ]
        )
    )
    provider = OpenAIResponsesProvider(environ={"OPENAI_API_KEY": "sk-test"}, client=client)

    events = [event async for event in provider.stream([], [], model="m", temperature=0, max_output_tokens=1)]

    assert events == [
        {
            "type": "tool_call",
            "tool_call": {
                "id": "call-1",
                "name": "read_file",
                "arguments": {"path": "README.md"},
            },
        },
        {
            "type": "response_metadata",
            "response_items": [
                {
                    "type": "function_call",
                    "id": "fc-1",
                    "call_id": "call-1",
                    "name": "read_file",
                }
            ],
        },
        {"type": "done", "finish_reason": None},
    ]


@pytest.mark.asyncio
async def test_openai_responses_provider_reports_malformed_tool_arguments() -> None:
    client = FakeClient(
        AsyncStream(
            [
                {
                    "type": "response.output_item.done",
                    "item": {
                        "type": "function_call",
                        "id": "fc-1",
                        "call_id": "call-1",
                        "name": "read_file",
                        "arguments": "{",
                    },
                },
            ]
        )
    )
    provider = OpenAIResponsesProvider(environ={"OPENAI_API_KEY": "sk-test"}, client=client)

    events = [event async for event in provider.stream([], [], model="m", temperature=0, max_output_tokens=1)]

    assert events[0]["type"] == "error"
    assert "Malformed JSON" in events[0]["message"]


@pytest.mark.asyncio
async def test_openai_responses_provider_preserves_reasoning_metadata() -> None:
    reasoning_item = {
        "type": "reasoning",
        "id": "rs-1",
        "summary": [{"type": "summary_text", "text": "checked tools"}],
        "encrypted_content": "encrypted",
    }
    client = FakeClient(
        AsyncStream(
            [
                {"type": "response.reasoning_summary_text.delta", "delta": "thinking"},
                {"type": "response.output_item.done", "item": reasoning_item},
            ]
        )
    )
    provider = OpenAIResponsesProvider(environ={"OPENAI_API_KEY": "sk-test"}, client=client)

    events = [event async for event in provider.stream([], [], model="m", temperature=0, max_output_tokens=1)]

    assert events == [
        {"type": "reasoning_delta", "content": "thinking"},
        {"type": "response_metadata", "response_items": [reasoning_item]},
        {"type": "done", "finish_reason": None},
    ]


@pytest.mark.asyncio
async def test_openai_responses_provider_normalizes_stream_errors() -> None:
    client = FakeClient(
        AsyncStream(
            [
                {
                    "type": "error",
                    "error": {"message": "bad request"},
                }
            ]
        )
    )
    provider = OpenAIResponsesProvider(environ={"OPENAI_API_KEY": "sk-test"}, client=client)

    events = [event async for event in provider.stream([], [], model="m", temperature=0, max_output_tokens=1)]

    assert events == [
        {"type": "error", "message": "bad request"},
        {"type": "done"},
    ]


@pytest.mark.asyncio
async def test_openai_responses_provider_normalizes_request_errors() -> None:
    provider = OpenAIResponsesProvider(
        environ={"OPENAI_API_KEY": "sk-test"},
        client=FakeClient(error=RuntimeError("boom")),
    )

    events = [event async for event in provider.stream([], [], model="m", temperature=0, max_output_tokens=1)]

    assert events == [
        {"type": "error", "message": "Provider request failed: boom"},
        {"type": "done"},
    ]
