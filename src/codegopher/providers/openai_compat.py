"""OpenAI-compatible streaming provider."""

from __future__ import annotations

import json
import os
from collections.abc import AsyncIterator
from collections.abc import Mapping
from typing import Any

from openai import AsyncOpenAI

from codegopher.core.errors import ProviderError
from codegopher.core.types import Message, StreamEvent, ToolSchema
from codegopher.providers.base import ProviderCapabilities


def _get(value: Any, key: str, default: Any = None) -> Any:
    if isinstance(value, dict):
        return value.get(key, default)
    return getattr(value, key, default)


class OpenAICompatProvider:
    capabilities = ProviderCapabilities(streaming=True, tool_calls=True, token_counting=True)

    def __init__(
        self,
        *,
        base_url: str | None = None,
        api_key_env: str | None = "OPENAI_API_KEY",
        environ: Mapping[str, str] | None = None,
        client: Any | None = None,
    ) -> None:
        env = environ or os.environ
        self.api_key_env = api_key_env or "OPENAI_API_KEY"
        self.api_key = env.get(self.api_key_env)
        if not self.api_key:
            raise ProviderError(f"Missing API key: expected environment variable {self.api_key_env}")
        self.base_url = base_url
        self._client = client or AsyncOpenAI(api_key=self.api_key, base_url=base_url)

    async def stream(
        self,
        messages: list[Message],
        tools: list[ToolSchema],
        *,
        model: str,
        temperature: float,
        max_output_tokens: int,
    ) -> AsyncIterator[StreamEvent]:
        stream = await self._client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice="auto" if tools else None,
            temperature=temperature,
            max_tokens=max_output_tokens,
            stream=True,
        )
        tool_buffers: dict[int, dict[str, str]] = {}
        async for chunk in stream:
            choices = _get(chunk, "choices", [])
            if not choices:
                continue
            delta = _get(choices[0], "delta", {})
            content = _get(delta, "content")
            if content:
                yield {"type": "text_delta", "content": str(content)}
            for raw_tool_call in _get(delta, "tool_calls", []) or []:
                index = int(_get(raw_tool_call, "index", 0))
                buffer = tool_buffers.setdefault(index, {"id": "", "name": "", "arguments": ""})
                if tool_id := _get(raw_tool_call, "id"):
                    buffer["id"] = str(tool_id)
                function = _get(raw_tool_call, "function", {})
                if name := _get(function, "name"):
                    buffer["name"] = str(name)
                if arguments := _get(function, "arguments"):
                    buffer["arguments"] += str(arguments)
        for buffer in tool_buffers.values():
            yield {
                "type": "tool_call",
                "tool_call": {
                    "id": buffer["id"],
                    "name": buffer["name"],
                    "arguments": json.loads(buffer["arguments"] or "{}"),
                },
            }
        yield {"type": "done"}
