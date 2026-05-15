"""Core headless agent loop."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from codegopher.config.schema import Settings
from codegopher.core.approval import (
    ApprovalRequest,
    ApprovalResult,
    resolve_approval,
    should_prompt,
)
from codegopher.core.context import build_messages
from codegopher.core.conversation import Conversation
from codegopher.core.errors import AgentLoopError, ProviderError
from codegopher.core.types import ToolCall
from codegopher.providers.base import Provider
from codegopher.tools.base import ToolContext, ToolResult
from codegopher.tools.registry import ToolRegistry
from codegopher.utils.json import dumps_json


class AgentResult(BaseModel):
    final_text: str
    tool_results: list[ToolResult] = Field(default_factory=list)
    iterations: int


@dataclass(frozen=True)
class AgentCallbacks:
    on_text_delta: Callable[[str], Awaitable[None]] | None = None
    on_tool_call: Callable[[ToolCall], Awaitable[None]] | None = None
    on_tool_result: Callable[[ToolResult], Awaitable[None]] | None = None
    on_approval_request: Callable[[ApprovalRequest], Awaitable[ApprovalResult]] | None = None
    on_error: Callable[[str], Awaitable[None]] | None = None
    on_complete: Callable[[AgentResult], Awaitable[None]] | None = None


async def _emit_callback(
    name: str,
    callback: Callable[..., Awaitable[None]] | None,
    *args: Any,
) -> None:
    if callback is None:
        return
    try:
        await callback(*args)
    except Exception as exc:
        raise AgentLoopError(f"Agent callback {name} failed: {exc}") from exc


async def _call_callback(
    name: str,
    callback: Callable[..., Awaitable[Any]],
    *args: Any,
) -> Any:
    try:
        return await callback(*args)
    except Exception as exc:
        raise AgentLoopError(f"Agent callback {name} failed: {exc}") from exc


async def run_agent(
    *,
    prompt: str,
    provider: Provider,
    registry: ToolRegistry,
    settings: Settings,
    cwd: Path,
    max_iterations: int = 8,
    stdin_is_tty: bool = False,
    callbacks: AgentCallbacks | None = None,
) -> AgentResult:
    if not provider.capabilities.tool_calls:
        raise ProviderError("Provider does not support tool calls")

    conversation = Conversation()
    conversation.append_user(prompt)
    tool_context = ToolContext(cwd=cwd)
    all_tool_results: list[ToolResult] = []

    for iteration in range(1, max_iterations + 1):
        text_parts: list[str] = []
        tool_calls: list[ToolCall] = []
        async for event in provider.stream(
            build_messages(
                conversation,
                cwd=cwd,
                registry=registry,
                approval_mode=settings.approval_mode,
            ),
            registry.schemas(),
            model=settings.model.name,
            temperature=settings.model.temperature,
            max_output_tokens=settings.model.max_output_tokens,
        ):
            if event["type"] == "text_delta":
                text_parts.append(event["content"])
                await _emit_callback(
                    "on_text_delta",
                    callbacks.on_text_delta if callbacks else None,
                    event["content"],
                )
            elif event["type"] == "tool_call":
                tool_calls.append(event["tool_call"])
                await _emit_callback(
                    "on_tool_call",
                    callbacks.on_tool_call if callbacks else None,
                    event["tool_call"],
                )
            elif event["type"] == "error":
                await _emit_callback(
                    "on_error",
                    callbacks.on_error if callbacks else None,
                    event["message"],
                )
                raise ProviderError(event["message"])

        final_text = "".join(text_parts)
        if not tool_calls:
            conversation.append_assistant(final_text)
            agent_result = AgentResult(
                final_text=final_text,
                tool_results=all_tool_results,
                iterations=iteration,
            )
            await _emit_callback(
                "on_complete",
                callbacks.on_complete if callbacks else None,
                agent_result,
            )
            return agent_result

        conversation.append_assistant(final_text or None, tool_calls)
        for tool_call in tool_calls:
            tool = registry.get(tool_call["name"])
            request = ApprovalRequest(tool_call["name"], dumps_json(tool_call["arguments"]))
            if (
                should_prompt(settings.approval_mode, tool)
                and callbacks
                and callbacks.on_approval_request
            ):
                approval = await _call_callback(
                    "on_approval_request",
                    callbacks.on_approval_request,
                    request,
                )
            else:
                approval = resolve_approval(
                    settings.approval_mode,
                    tool,
                    request,
                    stdin_is_tty=stdin_is_tty,
                )
            if not approval.approved:
                tool_result = ToolResult(
                    tool_call_id=tool_call["id"],
                    content=approval.reason or "Denied by user",
                    is_error=True,
                )
            else:
                arguments = dict(tool_call["arguments"])
                arguments["_tool_call_id"] = tool_call["id"]
                tool_result = await tool.execute(arguments, tool_context)
            all_tool_results.append(tool_result)
            conversation.append_tool_result(tool_result)
            await _emit_callback(
                "on_tool_result",
                callbacks.on_tool_result if callbacks else None,
                tool_result,
            )

    raise AgentLoopError(f"Agent exceeded max iterations: {max_iterations}")
