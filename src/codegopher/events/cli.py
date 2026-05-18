"""CLI presentation layer for CodeGopher JSONL events mode."""

from __future__ import annotations

from pathlib import Path
from typing import TextIO

from codegopher.config.schema import Settings
from codegopher.core.errors import AgentLoopError, ConfigurationError, ProviderError
from codegopher.events.protocol import (
    ApprovalRequestEvent,
    ApprovalResponseCommand,
    ErrorEvent,
    ProtocolEvent,
    ProtocolPayloadError,
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
    except (ConfigurationError, ProviderError, AgentLoopError):
        return 1

    return 0


async def _run_command_loop(
    *,
    session: EventsSession,
    stdin: TextIO,
    stdout: TextIO,
    cwd: Path,
) -> None:
    for line in stdin:
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
            try:
                await session.run_turn(command.prompt, turn_id=command.turn_id)
            except (ConfigurationError, ProviderError, AgentLoopError):
                continue
            continue

        await _emit_protocol_error(
            stdout,
            session_id=session.session_id,
            turn_id=command.turn_id,
            message=f"Unsupported command in events mode: {command.type}",
        )


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
