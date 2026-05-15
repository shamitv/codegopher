"""Provider protocol and shared capabilities."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Protocol

from pydantic import BaseModel

from codegopher.core.types import Message, StreamEvent, ToolSchema


class ProviderCapabilities(BaseModel):
    streaming: bool
    tool_calls: bool
    token_counting: bool = False


class Provider(Protocol):
    capabilities: ProviderCapabilities

    async def stream(
        self,
        messages: list[Message],
        tools: list[ToolSchema],
        *,
        model: str,
        temperature: float,
        max_output_tokens: int,
    ) -> AsyncIterator[StreamEvent]:
        ...

