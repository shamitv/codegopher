"""CLI presentation layer for CodeGopher JSONL events mode."""

from __future__ import annotations

from pathlib import Path
from typing import TextIO

from codegopher.config.schema import Settings


async def run_events_cli(
    *,
    prompt: str | None,
    settings: Settings,
    cwd: Path,
    stdin: TextIO,
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    """Run the events-mode CLI.

    The full JSONL protocol loop is implemented across the milestone 4 task
    series; this function is intentionally introduced first as the routing seam.
    """

    _ = (prompt, settings, cwd, stdin, stdout, stderr)
    return 0


__all__ = ["run_events_cli"]
