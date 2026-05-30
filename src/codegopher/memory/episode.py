"""Ephemeral task memory for one active agent session."""

from __future__ import annotations

import re
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from codegopher.core.types import EpisodeEntry, EpisodeKind, ToolCall


class EpisodeState:
    """Compact runtime-owned memory for a long task.

    Episode state is intentionally not backed by disk. It helps the next provider
    call see what the current session has already inspected without turning audit
    evidence or benchmark state into persistent memory.
    """

    def __init__(
        self,
        entries: list[EpisodeEntry] | None = None,
        *,
        max_entries: int = 80,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self.max_entries = max_entries
        self._now = now or (lambda: datetime.now(UTC))
        self.entries: list[EpisodeEntry] = list(entries or [])

    def add(
        self,
        kind: EpisodeKind,
        summary: str,
        *,
        refs: list[str] | None = None,
    ) -> EpisodeEntry:
        normalized_summary = _redact_episode_text(summary).strip()
        if not normalized_summary:
            raise ValueError("episode summary is required")
        entry = EpisodeEntry(
            id=f"episode-{uuid4().hex[:10]}",
            kind=kind,
            summary=normalized_summary[:500],
            refs=_normalize_refs(refs or []),
            created_at=self._now(),
        )
        self.entries.append(entry)
        if len(self.entries) > self.max_entries:
            self.entries = self.entries[-self.max_entries :]
        return entry

    def record_tool_result(
        self,
        tool_call: ToolCall,
        tool_result: Any,
        *,
        cwd: Path,
    ) -> None:
        name = tool_call["name"]
        args = tool_call["arguments"]
        if tool_result.is_error:
            self.add(
                "tool_error",
                f"{name} failed: {_first_line(tool_result.content)}",
                refs=_argument_refs(args, cwd=cwd),
            )
            return

        if name == "read_file":
            path = str(args.get("path", "")).strip()
            display_path = _display_path(path, cwd=cwd) if path else ""
            self.add(
                "file_read",
                f"Read {display_path or 'a file'} ({_line_count(tool_result.content)} lines returned).",
                refs=_normalize_refs([path], cwd=cwd) if path else [],
            )
            return

        if name == "read_many_files":
            refs = _argument_refs(args, cwd=cwd)
            self.add(
                "file_read",
                f"Read multiple files ({len(refs)} requested refs, {_section_count(tool_result.content)} sections returned).",
                refs=refs,
            )
            return

        if name in {"grep_search", "glob_search"}:
            refs = _result_refs(tool_result.content, cwd=cwd)
            label = "grep" if name == "grep_search" else "glob"
            query = str(args.get("query") or args.get("pattern") or "").strip()
            self.add(
                "search",
                f"Ran {label} search for `{query}` ({len(refs)} matching refs recorded).",
                refs=refs,
            )
            return

        if name == "list_dir":
            path = str(args.get("path", ".")).strip() or "."
            self.add(
                "directory_listing",
                f"Listed {path} ({_line_count(tool_result.content)} entries).",
                refs=[path],
            )
            return

        if name == "update_todo":
            self.add(
                "todo_update",
                _todo_summary(args, tool_result.content),
                refs=_todo_refs(args),
            )
            return

        if name == "write_chained_vulnerability_report":
            self.add("report_write", _first_line(tool_result.content))

    def record_final_text(self, text: str) -> None:
        summary = _first_nonempty_line(text)
        if summary:
            self.add("final_decision", f"Assistant final response: {summary}")

    def context_items(self, *, limit: int = 20) -> list[str]:
        items = self.entries[-limit:]
        return [
            _format_entry(entry)
            for entry in items
        ]


def _format_entry(entry: EpisodeEntry) -> str:
    text = f"[{entry.id}] {entry.kind}: {entry.summary}"
    if entry.refs:
        text += " refs=" + ", ".join(entry.refs[:6])
    return text


def _argument_refs(args: dict[str, Any], *, cwd: Path) -> list[str]:
    refs: list[str] = []
    for key in ("path", "paths", "globs", "pattern"):
        value = args.get(key)
        if isinstance(value, str):
            refs.append(value)
        elif isinstance(value, list):
            refs.extend(str(item) for item in value)
    return _normalize_refs(refs, cwd=cwd)


def _result_refs(content: str, *, cwd: Path) -> list[str]:
    refs: list[str] = []
    for line in content.splitlines()[:100]:
        if ":" in line:
            refs.append(line.split(":", maxsplit=1)[0])
        elif line.strip():
            refs.append(line.strip())
    return _normalize_refs(refs, cwd=cwd)


def _normalize_refs(refs: list[str], *, cwd: Path | None = None) -> list[str]:
    normalized: list[str] = []
    cwd_resolved = cwd.resolve() if cwd is not None else None
    for ref in refs:
        item = str(ref).strip()
        if not item:
            continue
        path = Path(item)
        if path.is_absolute():
            if cwd_resolved is not None:
                try:
                    item = path.resolve().relative_to(cwd_resolved).as_posix()
                except (OSError, ValueError):
                    item = "[ABSOLUTE_PATH]"
            else:
                item = "[ABSOLUTE_PATH]"
        item = _redact_episode_text(item)
        if item not in normalized:
            normalized.append(item)
    return normalized[:20]


def _display_path(raw_path: str, *, cwd: Path) -> str:
    path = Path(raw_path)
    item = raw_path
    if path.is_absolute():
        try:
            item = path.resolve().relative_to(cwd.resolve()).as_posix()
        except (OSError, ValueError):
            item = "[ABSOLUTE_PATH]"
    return _redact_episode_text(item)


def _todo_summary(args: dict[str, Any], result_content: str) -> str:
    action = str(args.get("action", "update")).strip() or "update"
    target = str(args.get("id") or args.get("text") or "").strip()
    reason = str(args.get("reason") or "").strip()
    summary = f"TODO {action}"
    if target:
        summary += f": {target}"
    if reason:
        summary += f" reason={reason}"
    return summary if target or reason else _first_line(result_content)


def _todo_refs(args: dict[str, Any]) -> list[str]:
    refs: list[str] = []
    for key in ("related_files", "evidence_refs"):
        value = args.get(key)
        if isinstance(value, list):
            refs.extend(str(item) for item in value)
    return _normalize_refs(refs)


def _redact_episode_text(value: str) -> str:
    redacted = re.sub(r"https?://[^\s)]+", "[URL]", value)
    redacted = re.sub(
        r"(?i)\b(api[_-]?key|token|secret|password)\s*[:=]\s*([^\s,;]+)",
        lambda match: f"{match.group(1)}=[REDACTED]",
        redacted,
    )
    redacted = re.sub(r"/tmp/[^\s)]+", "[TMP_PATH]", redacted)
    return redacted


def _line_count(value: str) -> int:
    if not value:
        return 0
    return len(value.splitlines())


def _section_count(value: str) -> int:
    return sum(1 for line in value.splitlines() if line.startswith("## "))


def _first_line(value: str) -> str:
    return _first_nonempty_line(value) or "(no output)"


def _first_nonempty_line(value: str) -> str | None:
    for line in value.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped[:300]
    return None
