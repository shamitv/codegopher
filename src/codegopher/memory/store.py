"""Local memory storage."""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path


class MemoryStore:
    """JSON-backed memory storage rooted in CodeGopher's data home."""

    def __init__(self, *, data_home: Path) -> None:
        self.data_home = data_home
        self.memory_root = data_home / "memory"

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
