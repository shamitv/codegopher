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
from codegopher.core.compaction import build_compaction_prompt, compacted_messages
from codegopher.core.compaction import compaction_id, split_for_compaction
from codegopher.core.context import build_messages
from codegopher.core.context_budget import calculate_context_budget
from codegopher.core.conversation import Conversation
from codegopher.core.errors import AgentLoopError, ProviderError
from codegopher.core.types import CompactionEntry, CompactionReason, Message, ToolCall
from codegopher.memory import MemoryStore
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
    on_reasoning_delta: Callable[[str], Awaitable[None]] | None = None
    on_tool_call: Callable[[ToolCall], Awaitable[None]] | None = None
    on_tool_result: Callable[[ToolResult], Awaitable[None]] | None = None
    on_approval_request: Callable[[ApprovalRequest], Awaitable[ApprovalResult]] | None = None
    on_compaction: Callable[[CompactionEntry], Awaitable[None]] | None = None
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


class AgentSession:
    """Reusable agent session with provider-ready conversation state."""

    def __init__(
        self,
        *,
        provider: Provider,
        registry: ToolRegistry,
        settings: Settings,
        cwd: Path,
        max_iterations: int = 8,
        stdin_is_tty: bool = False,
        callbacks: AgentCallbacks | None = None,
        tool_context: ToolContext | None = None,
        conversation: Conversation | None = None,
        memory_context: list[str] | None = None,
        skill_context: list[str] | None = None,
        todo_context: list[str] | None = None,
    ) -> None:
        self.provider = provider
        self.registry = registry
        self.settings = settings
        self.cwd = cwd
        self.max_iterations = max_iterations
        self.stdin_is_tty = stdin_is_tty
        self.callbacks = callbacks
        self.tool_context = tool_context or ToolContext(cwd=cwd, settings=settings)
        self.tool_context.settings = settings
        self.conversation = conversation or Conversation()
        self.memory_context = memory_context or []
        self._memory_context_override = memory_context is not None
        self.skill_context = skill_context or []
        self.todo_context = todo_context or []

    async def run_turn(self, prompt: str) -> AgentResult:
        if not self.provider.capabilities.tool_calls:
            raise ProviderError("Provider does not support tool calls")

        await self._compact_if_needed(prompt)
        self.conversation.append_user(prompt)
        all_tool_results: list[ToolResult] = []

        for iteration in range(1, self.max_iterations + 1):
            text_parts: list[str] = []
            tool_calls: list[ToolCall] = []
            async for event in self.provider.stream(
                build_messages(
                    self.conversation,
                    cwd=self.cwd,
                    registry=self.registry,
                    approval_mode=self.settings.approval_mode,
                    memories=self._current_memory_context(),
                ),
                self.registry.schemas(),
                model=self.settings.model.name,
                temperature=self.settings.model.temperature,
                max_output_tokens=self.settings.model.max_output_tokens,
            ):
                if event["type"] == "text_delta":
                    text_parts.append(event["content"])
                    await _emit_callback(
                        "on_text_delta",
                        self.callbacks.on_text_delta if self.callbacks else None,
                        event["content"],
                    )
                elif event["type"] == "reasoning_delta":
                    await _emit_callback(
                        "on_reasoning_delta",
                        self.callbacks.on_reasoning_delta if self.callbacks else None,
                        event["content"],
                    )
                elif event["type"] == "tool_call":
                    tool_calls.append(event["tool_call"])
                    await _emit_callback(
                        "on_tool_call",
                        self.callbacks.on_tool_call if self.callbacks else None,
                        event["tool_call"],
                    )
                elif event["type"] == "error":
                    await _emit_callback(
                        "on_error",
                        self.callbacks.on_error if self.callbacks else None,
                        event["message"],
                    )
                    raise ProviderError(event["message"])

            final_text = "".join(text_parts)
            if not tool_calls:
                self.conversation.append_assistant(final_text)
                agent_result = AgentResult(
                    final_text=final_text,
                    tool_results=all_tool_results,
                    iterations=iteration,
                )
                await _emit_callback(
                    "on_complete",
                    self.callbacks.on_complete if self.callbacks else None,
                    agent_result,
                )
                return agent_result

            self.conversation.append_assistant(final_text or None, tool_calls)
            for tool_call in tool_calls:
                tool = self.registry.get(tool_call["name"])
                request = ApprovalRequest(tool_call["name"], dumps_json(tool_call["arguments"]))
                if (
                    should_prompt(self.settings.approval_mode, tool)
                    and self.callbacks
                    and self.callbacks.on_approval_request
                ):
                    approval = await _call_callback(
                        "on_approval_request",
                        self.callbacks.on_approval_request,
                        request,
                    )
                else:
                    approval = resolve_approval(
                        self.settings.approval_mode,
                        tool,
                        request,
                        stdin_is_tty=self.stdin_is_tty,
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
                    tool_result = await tool.execute(arguments, self.tool_context)
                all_tool_results.append(tool_result)
                self.conversation.append_tool_result(tool_result)
                await _emit_callback(
                    "on_tool_result",
                    self.callbacks.on_tool_result if self.callbacks else None,
                    tool_result,
                )

        raise AgentLoopError(f"Agent exceeded max iterations: {self.max_iterations}")

    async def _compact_if_needed(self, prompt: str) -> None:
        pending_messages = [
            *self.conversation.provider_messages(),
            {"role": "user", "content": prompt},
        ]
        budget = calculate_context_budget(
            build_messages(
                Conversation(messages=pending_messages),
                cwd=self.cwd,
                registry=self.registry,
                approval_mode=self.settings.approval_mode,
                memories=self._current_memory_context(),
            ),
            settings=self.settings,
        )
        if not budget.compaction_exceeded:
            return
        if not split_for_compaction(self.conversation.provider_messages()).older_messages:
            return
        entry = await self.compact(reason="automatic")
        await _emit_callback(
            "on_compaction",
            self.callbacks.on_compaction if self.callbacks else None,
            entry,
        )

    async def compact(
        self,
        *,
        instructions: str | None = None,
        reason: CompactionReason = "manual",
    ) -> CompactionEntry:
        original_messages = self.conversation.provider_messages()
        prompt = build_compaction_prompt(
            original_messages,
            cwd=self.cwd,
            instructions=instructions,
            memories=self._current_memory_context(),
            skills=self.skill_context,
            todo_items=self.todo_context,
        )
        summary = await self._run_compaction_prompt(prompt)
        entry = CompactionEntry(
            id=compaction_id(),
            reason=reason,
            summary=summary,
            instructions=instructions,
        )
        self.conversation.messages = compacted_messages(
            original_messages,
            summary=summary,
            reason=reason,
            instructions=instructions,
        )
        return entry

    async def _run_compaction_prompt(self, prompt: str) -> str:
        text_parts: list[str] = []
        messages: list[Message] = [
            {"role": "system", "content": "You compact CodeGopher conversation history."},
            {"role": "user", "content": prompt},
        ]
        async for event in self.provider.stream(
            messages,
            [],
            model=self.settings.model.name,
            temperature=self.settings.model.temperature,
            max_output_tokens=self.settings.model.max_output_tokens,
        ):
            if event["type"] == "text_delta":
                text_parts.append(event["content"])
            elif event["type"] == "error":
                raise ProviderError(event["message"])
        summary = "".join(text_parts).strip()
        if not summary:
            raise ProviderError("Compaction returned an empty summary")
        return summary

    def _current_memory_context(self) -> list[str]:
        if self._memory_context_override:
            return list(self.memory_context)
        store = self.tool_context.memory_store or MemoryStore.default()
        entries = store.context_entries(
            settings=self.settings,
            cwd=self.cwd,
            session_id=self.tool_context.session_id,
        )
        self.memory_context = [
            f"[{entry.scope}:{entry.id}] {entry.content}" for entry in entries
        ]
        return list(self.memory_context)


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
    tool_context: ToolContext | None = None,
) -> AgentResult:
    session = AgentSession(
        provider=provider,
        registry=registry,
        settings=settings,
        cwd=cwd,
        max_iterations=max_iterations,
        stdin_is_tty=stdin_is_tty,
        callbacks=callbacks,
        tool_context=tool_context,
    )
    return await session.run_turn(prompt)
