from __future__ import annotations

import pytest

from codegopher.core.errors import ProviderError
from codegopher.providers.openai_compat import OpenAICompatProvider


class EmptyAsyncStream:
    def __aiter__(self) -> "EmptyAsyncStream":
        return self

    async def __anext__(self) -> object:
        raise StopAsyncIteration


class FakeCompletions:
    def __init__(self) -> None:
        self.kwargs = {}

    async def create(self, **kwargs):
        self.kwargs = kwargs
        return EmptyAsyncStream()


class FakeChat:
    def __init__(self) -> None:
        self.completions = FakeCompletions()


class FakeClient:
    def __init__(self) -> None:
        self.chat = FakeChat()


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
