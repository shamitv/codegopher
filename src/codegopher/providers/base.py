"""Provider protocol and shared capabilities."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Protocol

from pydantic import BaseModel

from codegopher.config.schema import ProviderApiFamily
from codegopher.core.types import Message, StreamEvent, ToolSchema


class ProviderCapabilities(BaseModel):
    streaming: bool
    tool_calls: bool
    token_counting: bool = False
    api_family: ProviderApiFamily = ProviderApiFamily.chat_completions
    reasoning_controls: bool = False
    json_schema: bool = False


class Provider(Protocol):
    capabilities: ProviderCapabilities

    def stream(
        self,
        messages: list[Message],
        tools: list[ToolSchema],
        *,
        model: str,
        temperature: float,
        max_output_tokens: int,
    ) -> AsyncIterator[StreamEvent]:
        ...
