"""In-process event session runner for IDE integrations."""

from __future__ import annotations

import asyncio
import inspect
import os
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, NoReturn, cast
from uuid import uuid4

from pydantic import ValidationError

from codegopher.config.inspection import (
    inspect_effective_config,
    list_mcp_servers,
)
from codegopher.config.management import (
    delete_mcp_server as delete_project_mcp_server,
)
from codegopher.config.management import (
    save_mcp_server as save_project_mcp_server,
)
from codegopher.config.management import (
    set_mcp_server_enabled as set_project_mcp_server_enabled,
)
from codegopher.config.schema import McpServerConfig, Settings
from codegopher.core.agent import AgentCallbacks, AgentResult, AgentSession
from codegopher.core.approval import ApprovalRequest, ApprovalResult
from codegopher.core.errors import AgentLoopError, ConfigurationError, ProviderError
from codegopher.core.mission import TaskLedger
from codegopher.core.types import ToolCall
from codegopher.events.protocol import (
    ApprovalRequestEvent,
    ConfigSnapshotEvent,
    ErrorEvent,
    McpServerDeletedEvent,
    McpServerPayload,
    McpServerSavedEvent,
    McpServersEvent,
    McpServerSnapshotPayload,
    ProtocolEvent,
    ProviderRecoveryEvent,
    ReasoningDeltaEvent,
    SessionStartedEvent,
    TaskContractCompletedEvent,
    TaskContractGateFailedEvent,
    TaskContractStartedEvent,
    TaskContractUpdatedEvent,
    TextDeltaEvent,
    ToolCallEvent,
    ToolResultEvent,
    TurnCompleteEvent,
    TurnStartedEvent,
    redact_protocol_value,
)
from codegopher.mcp import McpManager
from codegopher.providers.base import Provider
from codegopher.runtime import build_provider
from codegopher.tools.base import ToolContext, ToolResult
from codegopher.tools.registry import ToolRegistry, create_default_registry
from codegopher.utils.json import dumps_json
from codegopher.utils.paths import canonical_path

provider_error = "provider_error"
agent_loop_error = "agent_loop_error"
turn_cancelled = "turn_cancelled"
configuration_error = "configuration_error"
bad_approval_state = "bad_approval_state"

SUMMARY_LIMIT = 500

EventSink = Callable[[ProtocolEvent], Awaitable[None] | None]
ProviderFactory = Callable[[Settings], Provider]
RegistryFactory = Callable[[], ToolRegistry]
McpManagerFactory = Callable[[Settings, Path], McpManager]


@dataclass(frozen=True)
class EventsTurnResult:
    """Result metadata returned by an events-session turn."""

    turn_id: str
    final_text: str
    tool_count: int
    approval_count: int
    iteration_count: int
    cancelled: bool = False


@dataclass
class _PendingApproval:
    approval_id: str
    turn_id: str
    future: asyncio.Future[ApprovalResult]


class EventsSession:
    """Reusable event-emitting wrapper around the core agent session."""

    def __init__(
        self,
        *,
        settings: Settings,
        cwd: Path,
        event_sink: EventSink | None = None,
        provider_factory: ProviderFactory | None = None,
        registry_factory: RegistryFactory = create_default_registry,
        mcp_manager_factory: McpManagerFactory | None = None,
        environ: Mapping[str, str] | None = None,
        home: Path | None = None,
        session_id: str | None = None,
        max_iterations: int | None = None,
    ) -> None:
        self.settings = settings
        self.cwd = cwd
        self.event_sink = event_sink
        self.environ = os.environ if environ is None else environ
        self.home = home
        self.session_id = session_id or f"events-{uuid4().hex[:12]}"
        self.max_iterations = (
            max_iterations if max_iterations is not None else settings.agent.max_iterations
        )
        self.provider_factory = provider_factory or (
            lambda settings: build_provider(settings, environ=self.environ)
        )
        self.registry_factory = registry_factory
        self.mcp_manager_factory = mcp_manager_factory or (
            lambda settings, cwd: McpManager(
                settings=settings,
                cwd=cwd,
                environ=self.environ,
            )
        )
        self.events: list[ProtocolEvent] = []
        self.provider: Provider | None = None
        self.registry: ToolRegistry | None = None
        self.mcp_manager: McpManager | None = None
        self.tool_context: ToolContext | None = None
        self._agent_session: AgentSession | None = None
        self._started = False
        self._active_turn_id: str | None = None
        self._active_turn_task: asyncio.Task[AgentResult] | None = None
        self._pending_approval: _PendingApproval | None = None
        self._cancel_requested_turn_ids: set[str] = set()
        self._active_tool_count = 0
        self._active_approval_count = 0
        self._active_error_emitted = False

    async def __aenter__(self) -> EventsSession:
        return await self.start()

    async def __aexit__(self, *_exc_info: object) -> None:
        await self.aclose()

    async def start(self) -> EventsSession:
        """Initialize provider, registry, MCP tools, and tool context."""

        if self._started:
            return self
        self.registry = self.registry_factory()
        self.provider = self.provider_factory(self.settings)
        self.tool_context = ToolContext(
            cwd=self.cwd,
            settings=self.settings,
            session_id=self.session_id,
        )
        self.mcp_manager = self.mcp_manager_factory(self.settings, self.cwd)
        try:
            await self.mcp_manager.start()
            self.mcp_manager.register_tools(self.registry)
        except ConfigurationError as exc:
            await self._emit_error(configuration_error, str(exc))
            raise
        self._started = True
        await self._emit(
            SessionStartedEvent(
                session_id=self.session_id,
                cwd=canonical_path(self.cwd),
                provider=self.settings.model.provider,
                model=self.settings.model.name,
                approval_mode=self.settings.approval_mode.value,
            )
        )
        return self

    async def aclose(self) -> None:
        """Close owned MCP resources and cancel any active turn."""

        if self._active_turn_id and self._active_turn_task and not self._active_turn_task.done():
            self._cancel_requested_turn_ids.add(self._active_turn_id)
            self._active_turn_task.cancel()
        if self._pending_approval and not self._pending_approval.future.done():
            self._pending_approval.future.cancel()
        self._pending_approval = None
        if self.mcp_manager is not None:
            await self.mcp_manager.aclose()
        self.provider = None
        self.registry = None
        self.mcp_manager = None
        self.tool_context = None
        self._agent_session = None
        self._active_turn_id = None
        self._active_turn_task = None
        self._started = False

    async def run_turn(self, prompt: str, *, turn_id: str | None = None) -> EventsTurnResult:
        """Run one agent turn and emit protocol events for its lifecycle."""

        await self.start()
        if self._active_turn_task is not None and not self._active_turn_task.done():
            message = "An events session turn is already running"
            await self._emit_error(agent_loop_error, message, turn_id=self._active_turn_id)
            raise AgentLoopError(message)

        active_turn_id = turn_id or f"turn-{uuid4().hex[:12]}"
        self._active_turn_id = active_turn_id
        self._active_tool_count = 0
        self._active_approval_count = 0
        self._active_error_emitted = False
        await self._emit(
            TurnStartedEvent(
                session_id=self.session_id,
                turn_id=active_turn_id,
                cwd=canonical_path(self.cwd),
            )
        )

        task = asyncio.create_task(
            self._ensure_agent_session(active_turn_id).run_turn(prompt)
        )
        self._active_turn_task = task
        try:
            result = await task
        except asyncio.CancelledError:
            if active_turn_id not in self._cancel_requested_turn_ids:
                raise
            await self._emit_turn_error(
                turn_cancelled,
                "Turn cancelled",
                turn_id=active_turn_id,
            )
            return EventsTurnResult(
                turn_id=active_turn_id,
                final_text="",
                tool_count=self._active_tool_count,
                approval_count=self._active_approval_count,
                iteration_count=0,
                cancelled=True,
            )
        except ProviderError as exc:
            await self._emit_turn_error(provider_error, str(exc), turn_id=active_turn_id)
            raise
        except ConfigurationError as exc:
            await self._emit_turn_error(configuration_error, str(exc), turn_id=active_turn_id)
            raise
        except AgentLoopError as exc:
            await self._emit_turn_error(agent_loop_error, str(exc), turn_id=active_turn_id)
            raise
        finally:
            if self._pending_approval and self._pending_approval.turn_id == active_turn_id:
                if not self._pending_approval.future.done():
                    self._pending_approval.future.cancel()
                self._pending_approval = None
            self._cancel_requested_turn_ids.discard(active_turn_id)
            if self._active_turn_id == active_turn_id:
                self._active_turn_id = None
                self._active_turn_task = None

        return EventsTurnResult(
            turn_id=active_turn_id,
            final_text=result.final_text,
            tool_count=len(result.tool_results),
            approval_count=self._active_approval_count,
            iteration_count=result.iterations,
        )

    async def cancel_turn(self, turn_id: str) -> bool:
        """Cancel the active turn, if the id matches."""

        task = self._active_turn_task
        if self._active_turn_id != turn_id or task is None or task.done():
            await self._emit_error(
                bad_approval_state,
                f"No active turn found for cancellation: {turn_id}",
                turn_id=turn_id,
            )
            return False
        self._cancel_requested_turn_ids.add(turn_id)
        if self._pending_approval and self._pending_approval.turn_id == turn_id:
            if not self._pending_approval.future.done():
                self._pending_approval.future.cancel()
            self._pending_approval = None
        task.cancel()
        return True

    async def submit_approval(
        self,
        approval_id: str,
        *,
        approved: bool,
        reason: str | None = None,
    ) -> bool:
        """Resolve a pending approval response for the active turn."""

        pending = self._pending_approval
        if pending is None or pending.approval_id != approval_id or pending.future.done():
            await self._emit_error(
                bad_approval_state,
                f"No pending approval found: {approval_id}",
                turn_id=self._active_turn_id,
            )
            return False
        pending.future.set_result(ApprovalResult(approved=approved, reason=reason))
        self._pending_approval = None
        return True

    async def emit_effective_config(
        self,
        *,
        workspace_root: Path | str | None = None,
    ) -> ConfigSnapshotEvent:
        """Reload and emit the redacted effective LLM endpoint configuration."""

        cwd = self._workspace_path(workspace_root)
        try:
            snapshot = inspect_effective_config(
                cwd=cwd,
                home=self.home,
                environ=self.environ,
            )
        except ConfigurationError as exc:
            await self._emit_error(configuration_error, str(exc))
            raise
        event = ConfigSnapshotEvent(
            session_id=self.session_id,
            workspace_root=snapshot.workspace_root,
            provider=snapshot.provider,
            model=snapshot.model,
            api_family=cast(
                "Literal['chat_completions', 'responses']",
                snapshot.api_family,
            ),
            base_url=snapshot.base_url,
            replay_reasoning_content=snapshot.replay_reasoning_content,
            config_sources=list(snapshot.config_sources),
        )
        await self._emit(event)
        return event

    async def emit_mcp_servers(
        self,
        *,
        workspace_root: Path | str | None = None,
    ) -> McpServersEvent:
        """Reload and emit the redacted configured MCP server list."""

        cwd = self._workspace_path(workspace_root)
        try:
            snapshots = list_mcp_servers(
                cwd=cwd,
                home=self.home,
                environ=self.environ,
            )
        except ConfigurationError as exc:
            await self._emit_error(configuration_error, str(exc))
            raise
        event = McpServersEvent(
            session_id=self.session_id,
            workspace_root=str(cwd),
            servers=[
                McpServerSnapshotPayload(
                    name=snapshot.name,
                    source=snapshot.source,
                    server=snapshot.server,
                )
                for snapshot in snapshots
            ],
        )
        await self._emit(event)
        return event

    async def save_mcp_server(
        self,
        server_name: str,
        server: McpServerPayload,
        *,
        workspace_root: Path | str | None = None,
    ) -> McpServerSavedEvent:
        """Create or update a project-local MCP server and emit its redacted snapshot."""

        cwd = self._workspace_path(workspace_root)
        try:
            config = McpServerConfig.model_validate(server.model_dump(mode="json"))
            save_project_mcp_server(cwd, server_name, config)
            redacted = self._redacted_saved_server(cwd, server_name, fallback=server)
        except (ConfigurationError, ValidationError, OSError) as exc:
            await self._raise_config_failure(exc)
        event = McpServerSavedEvent(
            session_id=self.session_id,
            workspace_root=str(cwd),
            server_name=server_name,
            server=redacted,
        )
        await self._emit(event)
        return event

    async def set_mcp_server_enabled(
        self,
        server_name: str,
        enabled: bool,
        *,
        workspace_root: Path | str | None = None,
    ) -> McpServerSavedEvent:
        """Enable or disable a project-local MCP server and emit its redacted snapshot."""

        cwd = self._workspace_path(workspace_root)
        try:
            set_project_mcp_server_enabled(cwd, server_name, enabled)
            redacted = self._redacted_saved_server(cwd, server_name)
        except (ConfigurationError, ValidationError, OSError) as exc:
            await self._raise_config_failure(exc)
        event = McpServerSavedEvent(
            session_id=self.session_id,
            workspace_root=str(cwd),
            server_name=server_name,
            server=redacted,
        )
        await self._emit(event)
        return event

    async def delete_mcp_server(
        self,
        server_name: str,
        *,
        workspace_root: Path | str | None = None,
    ) -> McpServerDeletedEvent:
        """Delete a project-local MCP server and emit a deletion event."""

        cwd = self._workspace_path(workspace_root)
        try:
            delete_project_mcp_server(cwd, server_name)
        except (ConfigurationError, OSError) as exc:
            await self._raise_config_failure(exc)
        event = McpServerDeletedEvent(
            session_id=self.session_id,
            workspace_root=str(cwd),
            server_name=server_name,
        )
        await self._emit(event)
        return event

    def _ensure_agent_session(self, turn_id: str) -> AgentSession:
        callbacks = AgentCallbacks(
            on_text_delta=lambda content: self._on_text_delta(turn_id, content),
            on_reasoning_delta=lambda content: self._on_reasoning_delta(turn_id, content),
            on_tool_call=lambda tool_call: self._on_tool_call(turn_id, tool_call),
            on_tool_result=lambda result: self._on_tool_result(turn_id, result),
            on_approval_request=lambda request: self._on_approval_request(turn_id, request),
            on_error=lambda message: self._on_agent_error(turn_id, message),
            on_provider_recovery=lambda metadata: self._on_provider_recovery(
                turn_id, metadata
            ),
            on_complete=lambda result: self._on_complete(turn_id, result),
            on_task_contract_started=lambda ledger: self._on_task_contract_started(
                turn_id, ledger
            ),
            on_task_contract_updated=lambda ledger: self._on_task_contract_updated(
                turn_id, ledger
            ),
            on_task_contract_gate_failed=lambda ledger: self._on_task_contract_gate_failed(
                turn_id, ledger
            ),
            on_task_contract_completed=lambda ledger: self._on_task_contract_completed(
                turn_id, ledger
            ),
        )
        if self._agent_session is None:
            if self.provider is None or self.registry is None or self.tool_context is None:
                raise AgentLoopError("Events session has not been started")
            self._agent_session = AgentSession(
                provider=self.provider,
                registry=self.registry,
                settings=self.settings,
                cwd=self.cwd,
                max_iterations=self.max_iterations,
                stdin_is_tty=False,
                callbacks=callbacks,
                tool_context=self.tool_context,
            )
        else:
            self._agent_session.callbacks = callbacks
        return self._agent_session

    async def _on_text_delta(self, turn_id: str, content: str) -> None:
        await self._emit(
            TextDeltaEvent(
                session_id=self.session_id,
                turn_id=turn_id,
                content=content,
            )
        )

    async def _on_reasoning_delta(self, turn_id: str, content: str) -> None:
        await self._emit(
            ReasoningDeltaEvent(
                session_id=self.session_id,
                turn_id=turn_id,
                content=content,
            )
        )

    async def _on_tool_call(self, turn_id: str, tool_call: ToolCall) -> None:
        self._active_tool_count += 1
        await self._emit(
            ToolCallEvent(
                session_id=self.session_id,
                turn_id=turn_id,
                tool_id=tool_call["id"],
                tool_name=tool_call["name"],
                arguments_summary=_summary(tool_call["arguments"]),
            )
        )

    async def _on_tool_result(self, turn_id: str, result: ToolResult) -> None:
        await self._emit(
            ToolResultEvent(
                session_id=self.session_id,
                turn_id=turn_id,
                tool_id=result.tool_call_id,
                is_error=result.is_error,
                result_summary=_summary(result.content),
            )
        )

    async def _on_approval_request(
        self,
        turn_id: str,
        request: ApprovalRequest,
    ) -> ApprovalResult:
        if self._pending_approval is not None:
            await self._emit_turn_error(
                bad_approval_state,
                "A tool approval is already pending",
                turn_id=turn_id,
            )
            return ApprovalResult(
                approved=False,
                reason="A tool approval is already pending",
            )
        self._active_approval_count += 1
        approval_id = f"approval-{uuid4().hex[:12]}"
        future: asyncio.Future[ApprovalResult] = asyncio.get_running_loop().create_future()
        self._pending_approval = _PendingApproval(
            approval_id=approval_id,
            turn_id=turn_id,
            future=future,
        )
        raw_arguments = (
            redact_protocol_value(request.arguments)
            if request.arguments is not None
            else None
        )
        await self._emit(
            ApprovalRequestEvent(
                session_id=self.session_id,
                turn_id=turn_id,
                approval_id=approval_id,
                tool_name=request.tool_name,
                arguments_summary=_summary(request.arguments or request.arguments_preview),
                raw_arguments=raw_arguments,
            )
        )
        try:
            return await future
        finally:
            if self._pending_approval and self._pending_approval.approval_id == approval_id:
                self._pending_approval = None

    async def _on_agent_error(self, turn_id: str, message: str) -> None:
        await self._emit_turn_error(provider_error, message, turn_id=turn_id)

    async def _on_provider_recovery(
        self,
        turn_id: str,
        metadata: dict[str, Any],
    ) -> None:
        await self._emit(
            ProviderRecoveryEvent(
                session_id=self.session_id,
                turn_id=turn_id,
                code=str(metadata.get("code") or "provider_recovery"),
                message=str(metadata.get("message") or "provider recovery"),
                recovery_attempt=int(metadata.get("recovery_attempt") or 0),
                will_retry=bool(metadata.get("will_retry", True)),
                fallback_to_report=bool(metadata.get("fallback_to_report", False)),
                tool_name=metadata.get("tool_name"),
                tool_call_id=metadata.get("tool_call_id"),
                parse_error=dict(metadata.get("parse_error") or {}),
            )
        )

    async def _on_complete(self, turn_id: str, result: AgentResult) -> None:
        await self._emit(
            TurnCompleteEvent(
                session_id=self.session_id,
                turn_id=turn_id,
                final_text=result.final_text,
                tool_count=len(result.tool_results),
                approval_count=self._active_approval_count,
                iteration_count=result.iterations,
            )
        )

    async def _on_task_contract_started(
        self,
        turn_id: str,
        ledger: TaskLedger,
    ) -> None:
        await self._emit(
            TaskContractStartedEvent(
                session_id=self.session_id,
                turn_id=turn_id,
                task_id=ledger.id,
                title=ledger.contract.title,
                status=ledger.status,
                required_tool_calls=ledger.contract.required_tool_calls,
                required_artifacts=ledger.contract.required_artifacts,
            )
        )

    async def _on_task_contract_updated(
        self,
        turn_id: str,
        ledger: TaskLedger,
    ) -> None:
        await self._emit(
            TaskContractUpdatedEvent(
                session_id=self.session_id,
                turn_id=turn_id,
                task_id=ledger.id,
                status=ledger.status,
                observed_tool_calls=ledger.observed_tool_calls,
                observed_artifacts=ledger.observed_artifacts,
                recovery_attempts=ledger.recovery_attempts,
            )
        )

    async def _on_task_contract_gate_failed(
        self,
        turn_id: str,
        ledger: TaskLedger,
    ) -> None:
        await self._emit(
            TaskContractGateFailedEvent(
                session_id=self.session_id,
                turn_id=turn_id,
                task_id=ledger.id,
                gate_failures=ledger.gate_failures,
                recovery_attempts=ledger.recovery_attempts,
            )
        )

    async def _on_task_contract_completed(
        self,
        turn_id: str,
        ledger: TaskLedger,
    ) -> None:
        status: Literal["completed", "incomplete"] = (
            "completed" if ledger.status == "completed" else "incomplete"
        )
        await self._emit(
            TaskContractCompletedEvent(
                session_id=self.session_id,
                turn_id=turn_id,
                task_id=ledger.id,
                status=status,
                outcome=ledger.outcome,
            )
        )

    async def _emit_turn_error(self, code: str, message: str, *, turn_id: str) -> None:
        if self._active_error_emitted:
            return
        self._active_error_emitted = True
        await self._emit_error(code, message, turn_id=turn_id)

    async def _emit_error(
        self,
        code: str,
        message: str,
        *,
        turn_id: str | None = None,
    ) -> ErrorEvent:
        event = ErrorEvent(
            session_id=self.session_id,
            turn_id=turn_id,
            code=code,
            message=message or code,
        )
        await self._emit(event)
        return event

    async def _emit(self, event: ProtocolEvent) -> None:
        self.events.append(event)
        if self.event_sink is None:
            return
        result = self.event_sink(event)
        if inspect.isawaitable(result):
            await result

    def _workspace_path(self, workspace_root: Path | str | None) -> Path:
        if workspace_root is None:
            return self.cwd
        return Path(workspace_root)

    def _redacted_saved_server(
        self,
        cwd: Path,
        server_name: str,
        *,
        fallback: McpServerPayload | None = None,
    ) -> McpServerPayload:
        for snapshot in list_mcp_servers(cwd=cwd, home=self.home, environ=self.environ):
            if snapshot.name == server_name:
                return snapshot.server
        if fallback is not None:
            return McpServerPayload.model_validate(
                redact_protocol_value(fallback.model_dump(mode="json"))
            )
        raise ConfigurationError(f"MCP server not found: {server_name}")

    async def _raise_config_failure(self, exc: Exception) -> NoReturn:
        await self._emit_error(configuration_error, str(exc))
        if isinstance(exc, ConfigurationError):
            raise exc
        raise ConfigurationError(str(exc)) from exc


def _summary(value: Any, *, limit: int = SUMMARY_LIMIT) -> str:
    redacted = redact_protocol_value(value)
    rendered = redacted if isinstance(redacted, str) else dumps_json(redacted)
    if len(rendered) <= limit:
        return rendered
    return f"{rendered[: limit - 3]}..."


__all__ = [
    "EventsSession",
    "EventsTurnResult",
    "agent_loop_error",
    "bad_approval_state",
    "configuration_error",
    "provider_error",
    "turn_cancelled",
]
