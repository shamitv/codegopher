"""CLI presentation layer for CodeGopher JSONL events mode."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import TextIO

from codegopher.config.schema import Settings
from codegopher.core.errors import AgentLoopError, ConfigurationError, ProviderError
from codegopher.events.protocol import (
    ApprovalRequestEvent,
    ApprovalResponseCommand,
    CancelTurnCommand,
    DeleteMcpServerCommand,
    ErrorEvent,
    GetEffectiveConfigCommand,
    ListMcpServersCommand,
    ProtocolEvent,
    ProtocolPayloadError,
    SaveMcpServerCommand,
    SetMcpServerEnabledCommand,
    ShutdownCommand,
    StartTurnCommand,
    decode_jsonl_message,
    encode_jsonl_message,
)
from codegopher.events.session import EventsSession, ProviderFactory, configuration_error

protocol_error = "protocol_error"


async def run_events_cli(
    *,
    prompt: str | None,
    settings: Settings,
    cwd: Path,
    stdin: TextIO,
    stdout: TextIO,
    stderr: TextIO,
    provider_factory: ProviderFactory | None = None,
) -> int:
    """Run the events-mode CLI."""

    _ = (stdin, stderr)

    session: EventsSession

    async def emit_event(event: ProtocolEvent) -> None:
        stdout.write(encode_jsonl_message(event))
        stdout.flush()
        if prompt and isinstance(event, ApprovalRequestEvent):
            await _resolve_one_shot_approval(
                session=session,
                request=event,
                stdin=stdin,
                stdout=stdout,
            )

    session = EventsSession(
        settings=settings,
        cwd=cwd,
        event_sink=emit_event,
        provider_factory=provider_factory,
    )
    try:
        async with session:
            if prompt:
                await session.run_turn(prompt)
            else:
                await _run_command_loop(
                    session=session,
                    stdin=stdin,
                    stdout=stdout,
                    cwd=cwd,
                )
    except (ConfigurationError, ProviderError, AgentLoopError) as exc:
        stderr.write(f"{exc}\n")
        stderr.flush()
        return 1

    return 0


async def _run_command_loop(
    *,
    session: EventsSession,
    stdin: TextIO,
    stdout: TextIO,
    cwd: Path,
) -> None:
    active_turn_task: asyncio.Task[object] | None = None

    while True:
        active_turn_task = await _clear_completed_turn_task(active_turn_task)
        line = await asyncio.to_thread(stdin.readline)
        active_turn_task = await _clear_completed_turn_task(active_turn_task)

        if line == "":
            break

        if not line.strip():
            continue
        try:
            command = decode_jsonl_message(line)
        except ProtocolPayloadError as exc:
            await _emit_protocol_error(
                stdout,
                session_id=session.session_id,
                turn_id=None,
                message=str(exc),
            )
            continue

        if isinstance(command, StartTurnCommand):
            if active_turn_task is not None and not active_turn_task.done():
                await _await_turn_task(active_turn_task)
                active_turn_task = None
            if not _workspace_matches(command.workspace_root, cwd):
                await _emit_error(
                    stdout,
                    ErrorEvent(
                        session_id=session.session_id,
                        turn_id=command.turn_id,
                        code=configuration_error,
                        message="start_turn workspace_root must match the process cwd",
                    ),
                )
                continue
            active_turn_task = asyncio.create_task(
                session.run_turn(command.prompt, turn_id=command.turn_id)
            )
            await asyncio.sleep(0)
            continue

        if isinstance(command, CancelTurnCommand):
            await session.cancel_turn(command.turn_id)
            if active_turn_task is not None:
                await _await_turn_task(active_turn_task)
                active_turn_task = None
            continue

        if isinstance(command, ApprovalResponseCommand):
            await session.submit_approval(
                command.approval_id,
                approved=command.approved,
                reason=command.reason,
            )
            continue

        if isinstance(command, ShutdownCommand):
            if active_turn_task is not None:
                await _await_turn_task(active_turn_task)
            break

        if isinstance(command, GetEffectiveConfigCommand):
            if not await _require_workspace_match(session, stdout, command.workspace_root):
                continue
            try:
                await session.emit_effective_config(workspace_root=command.workspace_root)
            except ConfigurationError:
                continue
            continue

        if isinstance(command, ListMcpServersCommand):
            if not await _require_workspace_match(session, stdout, command.workspace_root):
                continue
            try:
                await session.emit_mcp_servers(workspace_root=command.workspace_root)
            except ConfigurationError:
                continue
            continue

        if isinstance(command, SaveMcpServerCommand):
            if not await _require_workspace_match(session, stdout, command.workspace_root):
                continue
            try:
                await session.save_mcp_server(
                    command.server_name,
                    command.server,
                    workspace_root=command.workspace_root,
                )
            except ConfigurationError:
                continue
            continue

        if isinstance(command, SetMcpServerEnabledCommand):
            if not await _require_workspace_match(session, stdout, command.workspace_root):
                continue
            try:
                await session.set_mcp_server_enabled(
                    command.server_name,
                    command.enabled,
                    workspace_root=command.workspace_root,
                )
            except ConfigurationError:
                continue
            continue

        if isinstance(command, DeleteMcpServerCommand):
            if not await _require_workspace_match(session, stdout, command.workspace_root):
                continue
            try:
                await session.delete_mcp_server(
                    command.server_name,
                    workspace_root=command.workspace_root,
                )
            except ConfigurationError:
                continue
            continue

        await _emit_protocol_error(
            stdout,
            session_id=session.session_id,
            turn_id=command.turn_id,
            message=f"Unsupported command in events mode: {command.type}",
        )

    if active_turn_task is not None:
        await _await_turn_task(active_turn_task)


async def _clear_completed_turn_task(
    task: asyncio.Task[object] | None,
) -> asyncio.Task[object] | None:
    if task is None or not task.done():
        return task
    await _await_turn_task(task)
    return None


async def _await_turn_task(task: asyncio.Task[object]) -> None:
    try:
        await task
    except (ConfigurationError, ProviderError, AgentLoopError):
        return


async def _resolve_one_shot_approval(
    *,
    session: EventsSession,
    request: ApprovalRequestEvent,
    stdin: TextIO,
    stdout: TextIO,
) -> None:
    line = stdin.readline()
    if not line:
        await _emit_protocol_error(
            stdout,
            session_id=request.session_id,
            turn_id=request.turn_id,
            message="Approval response required",
        )
        await session.submit_approval(
            request.approval_id,
            approved=False,
            reason="Approval response required",
        )
        return

    try:
        command = decode_jsonl_message(line)
    except ProtocolPayloadError as exc:
        await _emit_protocol_error(
            stdout,
            session_id=request.session_id,
            turn_id=request.turn_id,
            message=str(exc),
        )
        await session.submit_approval(
            request.approval_id,
            approved=False,
            reason="Invalid approval response",
        )
        return

    if not isinstance(command, ApprovalResponseCommand):
        await _emit_protocol_error(
            stdout,
            session_id=request.session_id,
            turn_id=request.turn_id,
            message=f"Expected approval_response, got {command.type}",
        )
        await session.submit_approval(
            request.approval_id,
            approved=False,
            reason="Invalid approval response",
        )
        return

    if command.approval_id != request.approval_id:
        await _emit_protocol_error(
            stdout,
            session_id=request.session_id,
            turn_id=request.turn_id,
            message=f"Approval id mismatch: {command.approval_id}",
        )
        await session.submit_approval(
            request.approval_id,
            approved=False,
            reason="Approval id mismatch",
        )
        return

    await session.submit_approval(
        command.approval_id,
        approved=command.approved,
        reason=command.reason,
    )


async def _require_workspace_match(
    session: EventsSession,
    stdout: TextIO,
    workspace_root: str,
) -> bool:
    if _workspace_matches(workspace_root, session.cwd):
        return True
    await _emit_error(
        stdout,
        ErrorEvent(
            session_id=session.session_id,
            code=configuration_error,
            message="Command workspace_root must match the process cwd",
        ),
    )
    return False


async def _emit_protocol_error(
    stdout: TextIO,
    *,
    session_id: str | None,
    turn_id: str | None,
    message: str,
) -> None:
    await _emit_error(
        stdout,
        ErrorEvent(
            session_id=session_id,
            turn_id=turn_id,
            code=protocol_error,
            message=message,
        )
    )


async def _emit_error(stdout: TextIO, event: ErrorEvent) -> None:
    stdout.write(encode_jsonl_message(event))
    stdout.flush()


def _workspace_matches(workspace_root: str, cwd: Path) -> bool:
    try:
        return Path(workspace_root).resolve() == cwd.resolve()
    except OSError:
        return False


__all__ = ["protocol_error", "run_events_cli"]
