from __future__ import annotations

from collections.abc import AsyncIterator

import pytest

from codegopher.core.errors import ProviderError
from codegopher.core.types import Message, StreamEvent, ToolSchema
from codegopher.providers.base import ProviderCapabilities
from codegopher.providers.registry import ProviderRegistry


class FakeProvider:
    capabilities = ProviderCapabilities(streaming=True, tool_calls=True)

    async def stream(
        self,
        messages: list[Message],
        tools: list[ToolSchema],
        *,
        model: str,
        temperature: float,
        max_output_tokens: int,
    ) -> AsyncIterator[StreamEvent]:
        yield {"type": "done"}


class TextOnlyProvider(FakeProvider):
    capabilities = ProviderCapabilities(streaming=True, tool_calls=False)


def test_provider_registry_creates_provider() -> None:
    registry = ProviderRegistry()
    registry.register("fake", FakeProvider)

    assert isinstance(registry.create("fake"), FakeProvider)


def test_provider_registry_rejects_provider_without_tool_calls() -> None:
    registry = ProviderRegistry()
    registry.register("text", TextOnlyProvider)

    with pytest.raises(ProviderError, match="does not support tool calls"):
        registry.create("text")
