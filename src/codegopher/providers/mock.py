"""Scripted provider for tests."""

from __future__ import annotations

from collections.abc import AsyncIterator

from codegopher.core.types import Message, StreamEvent, ToolSchema
from codegopher.providers.base import ProviderCapabilities


class MockProvider:
    capabilities = ProviderCapabilities(streaming=True, tool_calls=True)

    def __init__(self, turns: list[list[StreamEvent]]) -> None:
        self.turns = turns
        self.calls: list[list[Message]] = []

    async def stream(
        self,
        messages: list[Message],
        tools: list[ToolSchema],
        *,
        model: str,
        temperature: float,
        max_output_tokens: int,
    ) -> AsyncIterator[StreamEvent]:
        self.calls.append(messages)
        events = self.turns.pop(0) if self.turns else [{"type": "done"}]
        for event in events:
            yield event

