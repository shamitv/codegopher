"""Small `.codegopherignore` matcher."""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class IgnoreMatcher:
    patterns: tuple[str, ...]

    @classmethod
    def from_file(cls, root: Path, ignore_file: str = ".codegopherignore") -> IgnoreMatcher:
        path = root / ignore_file
        if not path.exists():
            return cls(())
        patterns = []
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if line and not line.startswith("#"):
                patterns.append(line.replace("\\", "/"))
        return cls(tuple(patterns))

    def matches(self, path: Path, root: Path) -> bool:
        try:
            rel = path.relative_to(root).as_posix()
        except ValueError:
            # Path is outside root; treat as non-matching
            return False
        for pattern in self.patterns:
            if pattern.endswith("/") and (rel + "/").startswith(pattern):
                return True
            if fnmatch.fnmatch(rel, pattern) or fnmatch.fnmatch(path.name, pattern):
                return True
        return False
