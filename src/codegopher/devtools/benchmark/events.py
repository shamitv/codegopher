"""Event-log parsing helpers for development benchmarks."""

from __future__ import annotations

import json
from collections import Counter
from typing import Any


def parse_events(stdout: str) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for line in stdout.splitlines():
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            events.append(value)
    return events


def event_counts(events: list[dict[str, Any]]) -> dict[str, int]:
    counts = Counter(str(event.get("type", "<unknown>")) for event in events)
    return dict(sorted(counts.items()))


def final_text_from_events(events: list[dict[str, Any]]) -> str:
    complete = next(
        (event for event in reversed(events) if event.get("type") == "turn_complete"),
        {},
    )
    return str(complete.get("final_text", ""))

