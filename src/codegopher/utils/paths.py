"""Path normalization helpers."""

from __future__ import annotations

import os
from pathlib import Path


def canonical_path(path: str | Path, *, root: Path | None = None, force_windows: bool = False) -> str:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = (root or Path.cwd()) / candidate
    resolved = candidate.resolve(strict=False)
    value = str(resolved)
    if force_windows or os.name == "nt":
        return os.path.normcase(value)
    return value


def canonical_parent(path: str | Path, *, root: Path | None = None) -> str:
    return canonical_path(Path(path).parent, root=root)

