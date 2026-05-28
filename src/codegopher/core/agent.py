"""Core headless agent loop."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from codegopher.config.schema import ProviderApiFamily, Settings
from codegopher.core.approval import (
    ApprovalRequest,
    ApprovalResult,
    resolve_approval,
    should_prompt,
)
from codegopher.core.compaction import (
    build_compaction_prompt,
    compacted_messages,
    compaction_id,
    split_for_compaction,
)
from codegopher.core.context import build_messages
from codegopher.core.context_budget import calculate_context_budget, selected_provider_entry
from codegopher.core.conversation import Conversation
from codegopher.core.errors import AgentLoopError, ProviderError, ToolExecutionError
from codegopher.core.mission import TaskLedger, select_mission_contract, todo_source
from codegopher.core.types import CompactionEntry, CompactionReason, Message, ToolCall
from codegopher.memory import EpisodeState, MemoryStore
from codegopher.providers.base import Provider
from codegopher.providers.openai_compat import model_requires_reasoning_content_replay
from codegopher.security.policy import (
    create_static_audit_registry,
    uses_chained_vulnerability_skill,
)
from codegopher.skills import SkillManager, discover_skills
from codegopher.todo import TodoState
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
    on_task_contract_started: Callable[[TaskLedger], Awaitable[None]] | None = None
    on_task_contract_updated: Callable[[TaskLedger], Awaitable[None]] | None = None
    on_task_contract_gate_failed: Callable[[TaskLedger], Awaitable[None]] | None = None
    on_task_contract_completed: Callable[[TaskLedger], Awaitable[None]] | None = None


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
        max_iterations: int | None = None,
        stdin_is_tty: bool = False,
        callbacks: AgentCallbacks | None = None,
        tool_context: ToolContext | None = None,
        conversation: Conversation | None = None,
        memory_context: list[str] | None = None,
        skill_context: list[str] | None = None,
        todo_context: list[str] | None = None,
        episode_context: list[str] | None = None,
        skill_manager: SkillManager | None = None,
        task_ledgers: list[TaskLedger] | None = None,
    ) -> None:
        self.provider = provider
        self.registry = registry
        self.settings = settings
        self.cwd = cwd
        self.max_iterations = (
            max_iterations if max_iterations is not None else settings.agent.max_iterations
        )
        self.stdin_is_tty = stdin_is_tty
        self.callbacks = callbacks
        self.tool_context = tool_context or ToolContext(cwd=cwd, settings=settings)
        self.tool_context.settings = settings
        if self.tool_context.todo_state is None:
            self.tool_context.todo_state = TodoState(max_items=settings.todo.max_items)
        if self.tool_context.episode_state is None:
            self.tool_context.episode_state = EpisodeState()
        self.conversation = conversation or Conversation()
        self.memory_context = memory_context or []
        self._memory_context_override = memory_context is not None
        self.skill_context = skill_context or []
        self._skill_context_override = skill_context is not None
        self.todo_context = todo_context or []
        self._todo_context_override = todo_context is not None
        self.episode_context = episode_context or []
        self._episode_context_override = episode_context is not None
        self.skill_manager = skill_manager or SkillManager(
            discover_skills(cwd=cwd, settings=settings).catalog,
            autoload=settings.skills.autoload,
        )
        self.task_ledgers = list(task_ledgers or [])
        self.active_task_ledger: TaskLedger | None = self._latest_active_task_ledger()
        self._provider_recovery_attempts = 0

    async def run_turn(self, prompt: str) -> AgentResult:
        if not self.provider.capabilities.tool_calls:
            raise ProviderError("Provider does not support tool calls")

        self._provider_recovery_attempts = 0
        self._load_skills_for_prompt(prompt)
        await self._activate_mission_for_prompt(prompt)
        self._seed_mission_todos()
        active_registry = self._active_registry_for_turn()
        await self._compact_if_needed(prompt, registry=active_registry)
        self.conversation.append_user(prompt)
        all_tool_results: list[ToolResult] = []

        for iteration in range(1, self.max_iterations + 1):
            text_parts: list[str] = []
            reasoning_parts: list[str] = []
            tool_calls: list[ToolCall] = []
            response_items: list[dict[str, Any]] = []
            recovery_prompt: str | None = None
            async for event in self.provider.stream(
                build_messages(
                    self.conversation,
                    cwd=self.cwd,
                    registry=active_registry,
                    approval_mode=self.settings.approval_mode,
                    memories=self._current_memory_context(),
                    skills=self._current_skill_context(),
                    todo_items=self._current_todo_context(),
                    mission_items=self._current_mission_context(),
                    episode_items=self._current_episode_context(),
                ),
                active_registry.schemas(),
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
                    reasoning_parts.append(event["content"])
                    await _emit_callback(
                        "on_reasoning_delta",
                        self.callbacks.on_reasoning_delta if self.callbacks else None,
                        event["content"],
                    )
                elif event["type"] == "tool_call":
                    tool_calls.append(event["tool_call"])
                    await self._record_task_tool_call(event["tool_call"]["name"])
                    await _emit_callback(
                        "on_tool_call",
                        self.callbacks.on_tool_call if self.callbacks else None,
                        event["tool_call"],
                    )
                elif event["type"] == "response_metadata":
                    response_items.extend(event["response_items"])
                elif event["type"] == "error":
                    recovery_prompt = await self._provider_error_recovery_prompt(
                        event["message"],
                        active_registry,
                    )
                    if recovery_prompt is not None:
                        break
                    await _emit_callback(
                        "on_error",
                        self.callbacks.on_error if self.callbacks else None,
                        event["message"],
                    )
                    raise ProviderError(event["message"])

            if recovery_prompt is not None:
                self.conversation.append_user(recovery_prompt)
                continue

            final_text = "".join(text_parts)
            reasoning_content = self._reasoning_content_for_replay(reasoning_parts)
            if not tool_calls:
                self._record_episode_final_text(final_text)
                self.conversation.append_assistant(
                    final_text,
                    response_items=response_items,
                    reasoning_content=reasoning_content,
                )
                completion_failures = await self._mission_completion_failures()
                if completion_failures:
                    recovery_prompt = await self._mission_recovery_prompt(
                        completion_failures
                    )
                    if recovery_prompt is not None:
                        self.conversation.append_user(recovery_prompt)
                        continue
                    final_text = self._incomplete_mission_final_text(completion_failures)
                agent_result = AgentResult(
                    final_text=final_text,
                    tool_results=all_tool_results,
                    iterations=iteration,
                )
                await self._mark_mission_completed_if_ready(completion_failures)
                await _emit_callback(
                    "on_complete",
                    self.callbacks.on_complete if self.callbacks else None,
                    agent_result,
                )
                return agent_result

            self.conversation.append_assistant(
                final_text or None,
                tool_calls,
                response_items=response_items,
                reasoning_content=reasoning_content,
            )
            for tool_call in tool_calls:
                try:
                    tool = active_registry.get(tool_call["name"])
                except ToolExecutionError as exc:
                    tool_result = ToolResult(
                        tool_call_id=tool_call["id"],
                        content=str(exc),
                        is_error=True,
                    )
                    all_tool_results.append(tool_result)
                    self.conversation.append_tool_result(tool_result)
                    self._record_episode_tool_result(tool_call, tool_result)
                    await _emit_callback(
                        "on_tool_result",
                        self.callbacks.on_tool_result if self.callbacks else None,
                        tool_result,
                    )
                    continue
                request = ApprovalRequest(
                    tool_name=tool_call["name"],
                    arguments_preview=dumps_json(tool_call["arguments"]),
                    tool_call_id=tool_call["id"],
                    arguments=dict(tool_call["arguments"]),
                )
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
                self._record_episode_tool_result(tool_call, tool_result)
                await self._record_task_tool_result(tool_result)
                await _emit_callback(
                    "on_tool_result",
                    self.callbacks.on_tool_result if self.callbacks else None,
                    tool_result,
                )

        raise AgentLoopError(f"Agent exceeded max iterations: {self.max_iterations}")

    async def _compact_if_needed(self, prompt: str, *, registry: ToolRegistry) -> None:
        pending_user_message: Message = {"role": "user", "content": prompt}
        pending_messages: list[Message] = [
            *self.conversation.provider_messages(),
            pending_user_message,
        ]
        budget = calculate_context_budget(
            build_messages(
                Conversation(messages=pending_messages),
                cwd=self.cwd,
                registry=registry,
                approval_mode=self.settings.approval_mode,
                memories=self._current_memory_context(),
                skills=self._current_skill_context(),
                todo_items=self._current_todo_context(),
                mission_items=self._current_mission_context(),
                episode_items=self._current_episode_context(),
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
            skills=self._current_skill_context(),
            todo_items=self._current_todo_context(),
            mission_items=self._current_mission_context(),
            episode_items=self._current_episode_context(),
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

    def _latest_active_task_ledger(self) -> TaskLedger | None:
        for ledger in reversed(self.task_ledgers):
            if ledger.status == "active":
                return ledger
        return None

    async def _activate_mission_for_prompt(self, prompt: str) -> None:
        contract = select_mission_contract(
            prompt=prompt,
            loaded_skill_ids=self.skill_manager.loaded_ids,
        )
        if contract is None:
            self.active_task_ledger = self._latest_active_task_ledger()
            return
        if (
            self.active_task_ledger is not None
            and self.active_task_ledger.status == "active"
            and self.active_task_ledger.contract.id == contract.id
        ):
            return
        ledger = TaskLedger.start(contract)
        self.task_ledgers.append(ledger)
        self.active_task_ledger = ledger
        await _emit_callback(
            "on_task_contract_started",
            self.callbacks.on_task_contract_started if self.callbacks else None,
            ledger,
        )

    def _seed_mission_todos(self) -> None:
        ledger = self.active_task_ledger
        if (
            ledger is None
            or self.tool_context.todo_state is None
            or not self.settings.todo.enabled
        ):
            return
        existing_sources = {
            item.source
            for item in self.tool_context.todo_state.list()
            if item.source is not None
        }
        existing_text = {item.text for item in self.tool_context.todo_state.list()}
        for index, text in enumerate(ledger.contract.required_todos, start=1):
            source = todo_source(ledger.contract, index)
            if source in existing_sources or text in existing_text:
                if source not in ledger.seeded_todo_sources:
                    ledger.seeded_todo_sources.append(source)
                continue
            self.tool_context.todo_state.add(
                text,
                source=source,
                reason=f"Mission contract: {ledger.contract.title}",
                evidence_refs=ledger.contract.required_artifacts,
            )
            ledger.seeded_todo_sources.append(source)
        ledger.touch()

    async def _record_task_tool_call(self, tool_name: str) -> None:
        ledger = self.active_task_ledger
        if ledger is None:
            return
        ledger.record_tool_call(tool_name)
        await _emit_callback(
            "on_task_contract_updated",
            self.callbacks.on_task_contract_updated if self.callbacks else None,
            ledger,
        )

    async def _record_task_tool_result(self, tool_result: ToolResult) -> None:
        ledger = self.active_task_ledger
        if ledger is None:
            return
        ledger.record_tool_result(tool_result.tool_call_id)
        await _emit_callback(
            "on_task_contract_updated",
            self.callbacks.on_task_contract_updated if self.callbacks else None,
            ledger,
        )

    async def _mission_completion_failures(self) -> list[str]:
        ledger = self.active_task_ledger
        if ledger is None or ledger.status != "active":
            return []
        failures = ledger.validate_completion(self.cwd)
        if failures:
            await _emit_callback(
                "on_task_contract_gate_failed",
                self.callbacks.on_task_contract_gate_failed if self.callbacks else None,
                ledger,
            )
        return failures

    async def _mission_recovery_prompt(self, failures: list[str]) -> str | None:
        ledger = self.active_task_ledger
        if ledger is None:
            return None
        if not ledger.can_recover():
            ledger.mark_incomplete(failures)
            await _emit_callback(
                "on_task_contract_completed",
                self.callbacks.on_task_contract_completed if self.callbacks else None,
                ledger,
            )
            return None
        prompt = ledger.build_recovery_prompt(failures)
        await _emit_callback(
            "on_task_contract_updated",
            self.callbacks.on_task_contract_updated if self.callbacks else None,
            ledger,
        )
        return prompt

    async def _provider_error_recovery_prompt(
        self,
        message: str,
        registry: ToolRegistry,
    ) -> str | None:
        if "Malformed JSON in tool arguments" not in message:
            return None
        if self._provider_recovery_attempts >= 2:
            ledger = self.active_task_ledger
            if ledger is not None:
                ledger.mark_incomplete([f"provider returned malformed tool-call JSON: {message}"])
            return None
        self._provider_recovery_attempts += 1
        return (
            "The previous provider turn emitted malformed JSON for a tool call, so "
            "CodeGopher could not execute it.\n\n"
            f"Error: {message}\n\n"
            "Reissue the needed tool call with strict JSON arguments only. Do not "
            "wrap the arguments in Markdown or add comments. Use one of these exact "
            "tool schemas:\n"
            f"{dumps_json(registry.schemas())}\n\n"
            "Continue from the current task state after the corrected tool call."
        )

    async def _mark_mission_completed_if_ready(self, failures: list[str]) -> None:
        ledger = self.active_task_ledger
        if ledger is None or failures or ledger.status != "active":
            return
        ledger.mark_completed()
        await _emit_callback(
            "on_task_contract_completed",
            self.callbacks.on_task_contract_completed if self.callbacks else None,
            ledger,
        )

    def _incomplete_mission_final_text(self, failures: list[str]) -> str:
        ledger = self.active_task_ledger
        title = ledger.contract.title if ledger is not None else "Active mission"
        missing = "\n".join(f"- {failure}" for failure in failures)
        return (
            f"{title} is incomplete after recovery attempts.\n\n"
            "Unresolved completion gates:\n"
            f"{missing}"
        )

    def _current_mission_context(self) -> list[str]:
        ledger = self.active_task_ledger
        if ledger is None or ledger.status != "active":
            return []
        return ledger.context_items()

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

    def _current_episode_context(self) -> list[str]:
        if self._episode_context_override:
            return list(self.episode_context)
        state = self.tool_context.episode_state
        if state is None:
            self.episode_context = []
            return []
        self.episode_context = state.context_items()
        return list(self.episode_context)

    def _load_skills_for_prompt(self, prompt: str) -> None:
        if self._skill_context_override:
            return
        self.skill_manager.load_for_prompt(prompt)
        self.skill_context = self.skill_manager.context_items()

    def _active_registry_for_turn(self) -> ToolRegistry:
        if uses_chained_vulnerability_skill(self.skill_manager.loaded_ids):
            return create_static_audit_registry(self.registry)
        return self.registry

    def _reasoning_content_for_replay(self, reasoning_parts: list[str]) -> str | None:
        entry = selected_provider_entry(self.settings)
        api_family = entry.api_family if entry is not None else ProviderApiFamily.chat_completions
        should_replay = (
            bool(entry and entry.replay_reasoning_content)
            or model_requires_reasoning_content_replay(self.settings.model.name)
        )
        if api_family is not ProviderApiFamily.chat_completions or not should_replay:
            return None
        reasoning_content = "".join(reasoning_parts)
        return reasoning_content or None

    def _current_skill_context(self) -> list[str]:
        if self._skill_context_override:
            return list(self.skill_context)
        self.skill_context = self.skill_manager.context_items()
        return list(self.skill_context)

    def _current_todo_context(self) -> list[str]:
        if self._todo_context_override:
            return list(self.todo_context)
        if not self.settings.todo.enabled or self.tool_context.todo_state is None:
            self.todo_context = []
            return []
        self.todo_context = self.tool_context.todo_state.context_items()
        return list(self.todo_context)

    def _record_episode_tool_result(
        self,
        tool_call: ToolCall,
        tool_result: ToolResult,
    ) -> None:
        state = self.tool_context.episode_state
        if state is None:
            return
        state.record_tool_result(tool_call, tool_result, cwd=self.cwd)

    def _record_episode_final_text(self, final_text: str) -> None:
        state = self.tool_context.episode_state
        if state is not None:
            state.record_final_text(final_text)


async def run_agent(
    *,
    prompt: str,
    provider: Provider,
    registry: ToolRegistry,
    settings: Settings,
    cwd: Path,
    max_iterations: int | None = None,
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
