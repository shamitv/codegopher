"""Local memory storage."""

from __future__ import annotations

import os
import hashlib
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
import json
from pathlib import Path
from uuid import uuid4

from codegopher.core.types import MemoryEntry, MemoryScope, MemorySource
from codegopher.utils.paths import canonical_path


class MemoryStore:
    """JSON-backed memory storage rooted in CodeGopher's data home."""

    def __init__(
        self,
        *,
        data_home: Path,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self.data_home = data_home
        self.memory_root = data_home / "memory"
        self._now = now or (lambda: datetime.now(UTC))

    @classmethod
    def default(
        cls,
        *,
        environ: Mapping[str, str] | None = None,
        home: Path | None = None,
    ) -> MemoryStore:
        env = os.environ if environ is None else environ
        if data_home := env.get("CODEGOPHER_DATA_HOME"):
            root = Path(data_home)
        elif xdg_data_home := env.get("XDG_DATA_HOME"):
            root = Path(xdg_data_home) / "codegopher"
        else:
            root = (home or Path.home()) / ".local" / "share" / "codegopher"
        return cls(data_home=root)

    @property
    def session_dir(self) -> Path:
        return self.memory_root / "session"

    @property
    def project_dir(self) -> Path:
        return self.memory_root / "project"

    def session_key(self, session_id: str) -> str:
        if not session_id:
            raise ValueError("session_id is required")
        return hashlib.sha256(session_id.encode("utf-8")).hexdigest()[:24]

    def session_file(self, session_id: str) -> Path:
        return self.session_dir / f"{self.session_key(session_id)}.json"

    def project_key(self, cwd: Path) -> str:
        return hashlib.sha256(canonical_path(cwd).encode("utf-8")).hexdigest()[:24]

    def project_file(self, cwd: Path) -> Path:
        return self.project_dir / f"{self.project_key(cwd)}.json"

    def list_entries(
        self,
        scope: MemoryScope,
        *,
        session_id: str | None = None,
        cwd: Path | None = None,
    ) -> list[MemoryEntry]:
        return self._load_entries(self._scope_file(scope, session_id=session_id, cwd=cwd))

    def add_entry(
        self,
        scope: MemoryScope,
        *,
        content: str,
        source: MemorySource = "user",
        session_id: str | None = None,
        cwd: Path | None = None,
        tags: list[str] | None = None,
        max_entries: int = 200,
        max_entry_chars: int = 4000,
    ) -> MemoryEntry:
        if len(content) > max_entry_chars:
            raise ValueError("memory content exceeds max_entry_chars")
        path = self._scope_file(scope, session_id=session_id, cwd=cwd)
        entries = self._load_entries(path)
        if len(entries) >= max_entries:
            raise ValueError("memory scope exceeds max_entries")
        now = self._now()
        entry = MemoryEntry(
            id=self._entry_id(),
            scope=scope,
            content=content,
            source=source,
            created_at=now,
            updated_at=now,
            tags=tags or [],
        )
        entries.append(entry)
        self._save_entries(path, entries)
        return entry

    def update_entry(
        self,
        scope: MemoryScope,
        entry_id: str,
        *,
        content: str,
        session_id: str | None = None,
        cwd: Path | None = None,
        tags: list[str] | None = None,
        max_entry_chars: int = 4000,
    ) -> MemoryEntry:
        if len(content) > max_entry_chars:
            raise ValueError("memory content exceeds max_entry_chars")
        path = self._scope_file(scope, session_id=session_id, cwd=cwd)
        entries = self._load_entries(path)
        for index, entry in enumerate(entries):
            if entry.id == entry_id:
                updated = entry.model_copy(
                    update={
                        "content": content,
                        "updated_at": self._now(),
                        "tags": entry.tags if tags is None else tags,
                    }
                )
                entries[index] = updated
                self._save_entries(path, entries)
                return updated
        raise KeyError(entry_id)

    def delete_entry(
        self,
        scope: MemoryScope,
        entry_id: str,
        *,
        session_id: str | None = None,
        cwd: Path | None = None,
    ) -> bool:
        path = self._scope_file(scope, session_id=session_id, cwd=cwd)
        entries = self._load_entries(path)
        remaining = [entry for entry in entries if entry.id != entry_id]
        if len(remaining) == len(entries):
            return False
        self._save_entries(path, remaining)
        return True

    def _scope_file(
        self,
        scope: MemoryScope,
        *,
        session_id: str | None,
        cwd: Path | None,
    ) -> Path:
        if scope == "session":
            if session_id is None:
                raise ValueError("session_id is required for session memory")
            return self.session_file(session_id)
        if scope == "project":
            if cwd is None:
                raise ValueError("cwd is required for project memory")
            return self.project_file(cwd)
        raise ValueError(f"unsupported memory scope: {scope}")

    def _load_entries(self, path: Path) -> list[MemoryEntry]:
        if not path.exists():
            return []
        data = json.loads(path.read_text(encoding="utf-8"))
        raw_entries = data.get("entries", []) if isinstance(data, dict) else []
        if not isinstance(raw_entries, list):
            raise ValueError("memory entries must be a list")
        return [MemoryEntry.model_validate(entry) for entry in raw_entries]

    def _save_entries(self, path: Path, entries: list[MemoryEntry]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": 1,
            "entries": [entry.model_dump(mode="json") for entry in entries],
        }
        tmp_path = path.with_suffix(".tmp")
        tmp_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        tmp_path.replace(path)

    def _entry_id(self) -> str:
        return f"mem-{uuid4().hex[:12]}"
