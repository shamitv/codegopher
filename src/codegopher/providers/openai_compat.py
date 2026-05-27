"""OpenAI-compatible streaming provider."""

from __future__ import annotations

import os
from collections.abc import AsyncIterator, Mapping
from typing import Any

from openai import AsyncOpenAI

from codegopher.core.errors import ProviderError
from codegopher.core.types import Message, StreamEvent, ToolSchema
from codegopher.providers.base import ProviderCapabilities
from codegopher.utils.json import JsonPayloadError, loads_object


def _get(value: Any, key: str, default: Any = None) -> Any:
    if isinstance(value, dict):
        return value.get(key, default)
    return getattr(value, key, default)


def _chat_messages(
    messages: list[Message],
    *,
    replay_reasoning_content: bool = False,
) -> list[dict[str, Any]]:
    allowed_keys = {"role", "content", "name", "tool_call_id", "tool_calls"}
    if replay_reasoning_content:
        allowed_keys.add("reasoning_content")
    return [
        {key: value for key, value in message.items() if key in allowed_keys}
        for message in messages
    ]


def model_requires_reasoning_content_replay(model: str) -> bool:
    """Return true for Chat Completions upstreams that require reasoning replay."""

    return model.lower().startswith("deepseek")


def _token_limit_parameter(model: str) -> str:
    model_l = model.lower()
    if model_l.startswith(("gpt-5", "o1", "o3", "o4")):
        return "max_completion_tokens"
    return "max_tokens"


class OpenAICompatProvider:
    capabilities = ProviderCapabilities(streaming=True, tool_calls=True, token_counting=True)

    def __init__(
        self,
        *,
        base_url: str | None = None,
        api_key_env: str | None = "OPENAI_API_KEY",
        environ: Mapping[str, str] | None = None,
        client: Any | None = None,
        replay_reasoning_content: bool = False,
    ) -> None:
        env = environ or os.environ
        self.api_key_env = api_key_env or "OPENAI_API_KEY"
        self.api_key = env.get(self.api_key_env)
        if not self.api_key:
            raise ProviderError(f"Missing API key: expected environment variable {self.api_key_env}")
        self.base_url = base_url
        self.replay_reasoning_content = replay_reasoning_content
        self._client: Any = client or AsyncOpenAI(api_key=self.api_key, base_url=base_url)

    async def stream(
        self,
        messages: list[Message],
        tools: list[ToolSchema],
        *,
        model: str,
        temperature: float,
        max_output_tokens: int,
    ) -> AsyncIterator[StreamEvent]:
        try:
            replay_reasoning_content = (
                self.replay_reasoning_content
                or model_requires_reasoning_content_replay(model)
            )
            request_args: dict[str, Any] = {
                "model": model,
                "messages": _chat_messages(
                    messages,
                    replay_reasoning_content=replay_reasoning_content,
                ),
                "temperature": temperature,
                "stream": True,
            }
            request_args[_token_limit_parameter(model)] = max_output_tokens
            if tools:
                request_args["tools"] = tools
                request_args["tool_choice"] = "auto"
            stream = await self._client.chat.completions.create(**request_args)
        except Exception as exc:
            yield {"type": "error", "message": f"Provider request failed: {exc}"}
            yield {"type": "done"}
            return
        tool_buffers: dict[int, dict[str, str]] = {}
        try:
            async for chunk in stream:
                choices = _get(chunk, "choices", [])
                if not choices:
                    continue
                delta = _get(choices[0], "delta", {})
                content = _get(delta, "content")
                if content:
                    yield {"type": "text_delta", "content": str(content)}
                reasoning = _get(delta, "reasoning_content")
                if reasoning:
                    yield {"type": "reasoning_delta", "content": str(reasoning)}
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
        except Exception as exc:
            yield {"type": "error", "message": f"Provider stream failed: {exc}"}
            yield {"type": "done"}
            return
        for buffer in tool_buffers.values():
            try:
                arguments = loads_object(buffer["arguments"] or "{}", source="tool arguments")
            except JsonPayloadError as exc:
                yield {"type": "error", "message": str(exc)}
                continue
            yield {
                "type": "tool_call",
                "tool_call": {
                    "id": buffer["id"],
                    "name": buffer["name"],
                    "arguments": arguments,
                },
            }
        yield {"type": "done"}
