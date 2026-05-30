"""OpenAI Responses API streaming provider."""

from __future__ import annotations

import os
from collections.abc import AsyncIterator, Mapping
from typing import Any

from openai import AsyncOpenAI

from codegopher.config.schema import ProviderApiFamily
from codegopher.core.errors import ProviderError
from codegopher.core.types import Message, StreamEvent, ToolSchema
from codegopher.providers.base import ProviderCapabilities
from codegopher.utils.json import JsonPayloadError, loads_object


def _get(value: Any, key: str, default: Any = None) -> Any:
    if isinstance(value, dict):
        return value.get(key, default)
    return getattr(value, key, default)


def _to_plain_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    if hasattr(value, "model_dump"):
        dumped = value.model_dump(mode="json", exclude_none=True)
        return dumped if isinstance(dumped, dict) else {}
    if hasattr(value, "to_dict"):
        dumped = value.to_dict()
        return dumped if isinstance(dumped, dict) else {}
    raw = getattr(value, "__dict__", None)
    if isinstance(raw, dict):
        return {key: item for key, item in raw.items() if not key.startswith("_")}
    return {}


def _event_type(event: Any) -> str:
    return str(_get(event, "type", ""))


def _event_text(event: Any) -> str:
    for key in ("delta", "text", "content", "message"):
        value = _get(event, key)
        if value:
            return str(value)
    return ""


def _item_key(event: Any, item: Any | None = None) -> str:
    for source in (event, item):
        if source is None:
            continue
        for key in ("item_id", "call_id", "id", "output_index"):
            value = _get(source, key)
            if value is not None:
                return str(value)
    return ""


def _response_function_tool(tool: ToolSchema) -> dict[str, Any]:
    function = tool["function"]
    response_tool: dict[str, Any] = {
        "type": "function",
        "name": function["name"],
        "parameters": function.get("parameters", {"type": "object", "properties": {}}),
    }
    if description := function.get("description"):
        response_tool["description"] = description
    return response_tool


def _message_item(role: str, content: str) -> dict[str, Any]:
    content_type = "output_text" if role == "assistant" else "input_text"
    return {"type": "message", "role": role, "content": [{"type": content_type, "text": content}]}


def _responses_input(messages: list[Message]) -> tuple[str | None, list[dict[str, Any]]]:
    instructions: list[str] = []
    input_items: list[dict[str, Any]] = []
    for message in messages:
        role = message.get("role")
        content = message.get("content")
        if role == "system":
            if content:
                instructions.append(content)
            continue
        if role == "tool":
            input_items.append(
                {
                    "type": "function_call_output",
                    "call_id": message.get("tool_call_id", ""),
                    "output": content or "",
                }
            )
            continue
        if role == "assistant":
            response_items = message.get("response_items", [])
            input_items.extend(response_items)
            if response_items:
                continue
            if content:
                input_items.append(_message_item("assistant", content))
            for tool_call in message.get("tool_calls", []) or []:
                function = _get(tool_call, "function", {})
                input_items.append(
                    {
                        "type": "function_call",
                        "call_id": _get(tool_call, "id", ""),
                        "name": _get(function, "name", ""),
                        "arguments": _get(function, "arguments", "{}") or "{}",
                    }
                )
            continue
        if role == "user":
            input_items.append(_message_item("user", content or ""))
    return "\n\n".join(instructions) or None, input_items


def _metadata_item(item: Any) -> dict[str, Any] | None:
    plain = _to_plain_dict(item)
    item_type = str(plain.get("type", ""))
    if item_type == "function_call":
        return plain
    if "reasoning" in item_type and (plain.get("encrypted_content") or plain.get("summary")):
        return plain
    return None


class OpenAIResponsesProvider:
    """Streaming provider backed by OpenAI Responses with local state replay."""

    capabilities = ProviderCapabilities(
        streaming=True,
        tool_calls=True,
        token_counting=True,
        api_family=ProviderApiFamily.responses,
        reasoning_controls=True,
        json_schema=True,
    )

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
        instructions, input_items = _responses_input(messages)
        request_args: dict[str, Any] = {
            "model": model,
            "input": input_items,
            "stream": True,
            "store": False,
            "max_output_tokens": max_output_tokens,
            "temperature": temperature,
        }
        if instructions:
            request_args["instructions"] = instructions
        if tools:
            request_args["tools"] = [_response_function_tool(tool) for tool in tools]
            request_args["tool_choice"] = "auto"

        try:
            stream = await self._client.responses.create(**request_args)
        except Exception as exc:
            yield {"type": "error", "message": f"Provider request failed: {exc}"}
            yield {"type": "done"}
            return

        argument_buffers: dict[str, str] = {}
        argument_done_keys: set[str] = set()
        response_items: list[dict[str, Any]] = []
        completed_reason: str | None = None
        try:
            async for event in stream:
                event_type = _event_type(event)
                if event_type == "response.output_text.delta":
                    if text := _event_text(event):
                        yield {"type": "text_delta", "content": text}
                elif event_type in {
                    "response.reasoning_summary_text.delta",
                    "response.reasoning_text.delta",
                }:
                    if text := _event_text(event):
                        yield {"type": "reasoning_delta", "content": text}
                elif event_type == "response.function_call_arguments.delta":
                    key = _item_key(event)
                    if key:
                        argument_buffers[key] = argument_buffers.get(key, "") + _event_text(event)
                elif event_type == "response.function_call_arguments.done":
                    key = _item_key(event)
                    if key:
                        argument_buffers[key] = str(_get(event, "arguments", argument_buffers.get(key, "")))
                        argument_done_keys.add(key)
                elif event_type == "response.output_item.done":
                    item = _get(event, "item", {})
                    if metadata := _metadata_item(item):
                        response_items.append(metadata)
                    if str(_get(item, "type", "")) == "function_call":
                        try:
                            yield self._tool_call_event(
                                item,
                                argument_buffers,
                            )
                        except JsonPayloadError as exc:
                            yield self._tool_call_parse_error_event(
                                item,
                                argument_buffers,
                                argument_done_keys,
                                exc,
                            )
                elif event_type == "response.completed":
                    completed_reason = str(_get(event, "finish_reason", "stop"))
                elif event_type in {"error", "response.failed", "response.incomplete"}:
                    message = str(
                        _get(_get(event, "error", {}), "message")
                        or _get(event, "message")
                        or f"Provider stream failed: {event_type}"
                    )
                    yield {"type": "error", "message": message}
                    yield {"type": "done"}
                    return
        except Exception as exc:
            yield {"type": "error", "message": f"Provider stream failed: {exc}"}
            yield {"type": "done"}
            return

        if response_items:
            yield {"type": "response_metadata", "response_items": response_items}
        yield {"type": "done", "finish_reason": completed_reason}

    def _tool_call_event(
        self,
        item: Any,
        argument_buffers: dict[str, str],
    ) -> StreamEvent:
        item_id = str(_get(item, "id", ""))
        call_id = str(_get(item, "call_id", "") or item_id)
        arguments_payload = str(
            _get(item, "arguments")
            or argument_buffers.get(item_id)
            or argument_buffers.get(call_id)
            or "{}"
        )
        return {
            "type": "tool_call",
            "tool_call": {
                "id": call_id,
                "name": str(_get(item, "name", "")),
                "arguments": loads_object(arguments_payload, source="tool arguments"),
            },
        }

    def _tool_call_parse_error_event(
        self,
        item: Any,
        argument_buffers: dict[str, str],
        argument_done_keys: set[str],
        exc: JsonPayloadError,
    ) -> StreamEvent:
        item_id = str(_get(item, "id", ""))
        call_id = str(_get(item, "call_id", "") or item_id)
        arguments_payload = str(
            _get(item, "arguments")
            or argument_buffers.get(item_id)
            or argument_buffers.get(call_id)
            or ""
        )
        return {
            "type": "error",
            "code": "malformed_tool_arguments",
            "message": str(exc),
            "tool_name": str(_get(item, "name", "")) or None,
            "tool_call_id": call_id or None,
            "tool_call_parse_error": {
                **exc.to_metadata(),
                "item_id": item_id or None,
                "call_id": call_id or None,
                "tool_name": str(_get(item, "name", "")) or None,
                "stream_arguments_done": (
                    item_id in argument_done_keys or call_id in argument_done_keys
                ),
                "payload_length": len(arguments_payload),
            },
        }


def build_responses_request_preview(
    messages: list[Message],
    tools: list[ToolSchema],
    *,
    model: str,
    temperature: float,
    max_output_tokens: int,
) -> dict[str, Any]:
    """Return the provider request shape without contacting OpenAI."""

    instructions, input_items = _responses_input(messages)
    request_args: dict[str, Any] = {
        "model": model,
        "input": input_items,
        "stream": True,
        "store": False,
        "max_output_tokens": max_output_tokens,
        "temperature": temperature,
    }
    if instructions:
        request_args["instructions"] = instructions
    if tools:
        request_args["tools"] = [_response_function_tool(tool) for tool in tools]
        request_args["tool_choice"] = "auto"
    return request_args
