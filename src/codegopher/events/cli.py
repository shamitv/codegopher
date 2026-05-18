"""CLI presentation layer for CodeGopher JSONL events mode."""

from __future__ import annotations

from pathlib import Path
from typing import TextIO

from codegopher.config.schema import Settings
from codegopher.core.errors import AgentLoopError, ConfigurationError, ProviderError
from codegopher.events.protocol import ProtocolEvent, encode_jsonl_message
from codegopher.events.session import EventsSession


async def run_events_cli(
    *,
    prompt: str | None,
    settings: Settings,
    cwd: Path,
    stdin: TextIO,
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    """Run the events-mode CLI."""

    _ = (stdin, stderr)

    async def emit_event(event: ProtocolEvent) -> None:
        stdout.write(encode_jsonl_message(event))
        stdout.flush()

    session = EventsSession(
        settings=settings,
        cwd=cwd,
        event_sink=emit_event,
    )
    if prompt:
        try:
            async with session:
                await session.run_turn(prompt)
        except (ConfigurationError, ProviderError, AgentLoopError):
            return 1
        return 0

    return 0


__all__ = ["run_events_cli"]
