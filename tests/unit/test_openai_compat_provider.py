from __future__ import annotations

import pytest

from codegopher.core.errors import ProviderError
from codegopher.providers.openai_compat import OpenAICompatProvider


class AsyncStream:
    def __init__(self, items: list[object] | None = None) -> None:
        self.items = list(items or [])

    def __aiter__(self) -> AsyncStream:
        return self

    async def __anext__(self) -> object:
        if not self.items:
            raise StopAsyncIteration
        return self.items.pop(0)


class FakeCompletions:
    def __init__(self, stream: AsyncStream | None = None, error: Exception | None = None) -> None:
        self.kwargs = {}
        self.stream = stream or AsyncStream()
        self.error = error

    async def create(self, **kwargs):
        self.kwargs = kwargs
        if self.error:
            raise self.error
        return self.stream


class FakeChat:
    def __init__(self, stream: AsyncStream | None = None, error: Exception | None = None) -> None:
        self.completions = FakeCompletions(stream, error)


class FakeClient:
    def __init__(self, stream: AsyncStream | None = None, error: Exception | None = None) -> None:
        self.chat = FakeChat(stream, error)


def test_openai_compat_provider_resolves_api_key() -> None:
    provider = OpenAICompatProvider(environ={"OPENAI_API_KEY": "sk-test"}, client=object())

    assert provider.api_key == "sk-test"
    assert provider.api_key_env == "OPENAI_API_KEY"


def test_openai_compat_provider_reports_missing_api_key() -> None:
    with pytest.raises(ProviderError, match="OPENAI_API_KEY"):
        OpenAICompatProvider(environ={}, client=object())


@pytest.mark.asyncio
async def test_openai_compat_provider_builds_request() -> None:
    client = FakeClient()
    provider = OpenAICompatProvider(environ={"OPENAI_API_KEY": "sk-test"}, client=client)

    events = [
        event
        async for event in provider.stream(
            [{"role": "user", "content": "hello"}],
            [{"type": "function", "function": {"name": "read_file"}}],
            model="gpt-test",
            temperature=0.2,
            max_output_tokens=128,
        )
    ]

    assert events == [{"type": "done"}]
    assert client.chat.completions.kwargs["model"] == "gpt-test"
    assert client.chat.completions.kwargs["temperature"] == 0.2
    assert client.chat.completions.kwargs["max_tokens"] == 128
    assert client.chat.completions.kwargs["stream"] is True


@pytest.mark.asyncio
async def test_openai_compat_provider_strips_responses_metadata_from_messages() -> None:
    client = FakeClient()
    provider = OpenAICompatProvider(environ={"OPENAI_API_KEY": "sk-test"}, client=client)

    _ = [
        event
        async for event in provider.stream(
            [
                {
                    "role": "assistant",
                    "content": "answer",
                    "response_items": [{"type": "reasoning", "encrypted_content": "secret"}],
                }
            ],
            [],
            model="gpt-test",
            temperature=0.2,
            max_output_tokens=128,
        )
    ]

    assert client.chat.completions.kwargs["messages"] == [
        {"role": "assistant", "content": "answer"}
    ]


@pytest.mark.asyncio
async def test_openai_compat_provider_parses_text_deltas() -> None:
    client = FakeClient(
        AsyncStream(
            [
                {"choices": [{"delta": {"content": "hel"}}]},
                {"choices": [{"delta": {"content": "lo"}}]},
            ]
        )
    )
    provider = OpenAICompatProvider(environ={"OPENAI_API_KEY": "sk-test"}, client=client)

    events = [event async for event in provider.stream([], [], model="m", temperature=0, max_output_tokens=1)]

    assert events == [
        {"type": "text_delta", "content": "hel"},
        {"type": "text_delta", "content": "lo"},
        {"type": "done"},
    ]


@pytest.mark.asyncio
async def test_openai_compat_provider_parses_reasoning_deltas() -> None:
    client = FakeClient(
        AsyncStream(
            [
                {"choices": [{"delta": {"reasoning_content": "think "}}]},
                {"choices": [{"delta": {"reasoning_content": "more"}}]},
            ]
        )
    )
    provider = OpenAICompatProvider(environ={"OPENAI_API_KEY": "sk-test"}, client=client)

    events = [event async for event in provider.stream([], [], model="m", temperature=0, max_output_tokens=1)]

    assert events == [
        {"type": "reasoning_delta", "content": "think "},
        {"type": "reasoning_delta", "content": "more"},
        {"type": "done"},
    ]


@pytest.mark.asyncio
async def test_openai_compat_provider_parses_streamed_tool_calls() -> None:
    client = FakeClient(
        AsyncStream(
            [
                {
                    "choices": [
                        {
                            "delta": {
                                "tool_calls": [
                                    {
                                        "index": 0,
                                        "id": "call-1",
                                        "type": "function",
                                        "function": {"name": "echo", "arguments": "{"},
                                    }
                                ]
                            }
                        }
                    ]
                },
                {
                    "choices": [
                        {
                            "delta": {
                                "tool_calls": [
                                    {"index": 0, "function": {"arguments": '"text":"hi"}'}}
                                ]
                            }
                        }
                    ]
                },
            ]
        )
    )
    provider = OpenAICompatProvider(environ={"OPENAI_API_KEY": "sk-test"}, client=client)

    events = [event async for event in provider.stream([], [], model="m", temperature=0, max_output_tokens=1)]

    assert events == [
        {
            "type": "tool_call",
            "tool_call": {"id": "call-1", "name": "echo", "arguments": {"text": "hi"}},
        },
        {"type": "done"},
    ]


@pytest.mark.asyncio
async def test_openai_compat_provider_reports_malformed_tool_arguments() -> None:
    client = FakeClient(
        AsyncStream(
            [
                {
                    "choices": [
                        {
                            "delta": {
                                "tool_calls": [
                                    {
                                        "index": 0,
                                        "id": "call-1",
                                        "function": {"name": "echo", "arguments": "{"},
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        )
    )
    provider = OpenAICompatProvider(environ={"OPENAI_API_KEY": "sk-test"}, client=client)

    events = [event async for event in provider.stream([], [], model="m", temperature=0, max_output_tokens=1)]

    assert events[0]["type"] == "error"
    assert "Malformed JSON" in events[0]["message"]


@pytest.mark.asyncio
async def test_openai_compat_provider_normalizes_request_errors() -> None:
    provider = OpenAICompatProvider(
        environ={"OPENAI_API_KEY": "sk-test"},
        client=FakeClient(error=RuntimeError("boom")),
    )

    events = [event async for event in provider.stream([], [], model="m", temperature=0, max_output_tokens=1)]

    assert events == [
        {"type": "error", "message": "Provider request failed: boom"},
        {"type": "done"},
    ]
