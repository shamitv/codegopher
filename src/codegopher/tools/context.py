"""Session-scoped tool execution context."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from codegopher.core.errors import ToolExecutionError
from codegopher.utils.paths import canonical_path


@dataclass
class AccessTracker:
    root: Path = field(default_factory=Path.cwd)
    read_files: set[str] = field(default_factory=set)
    inspected_dirs: set[str] = field(default_factory=set)

    def canonical_file(self, path: str | Path) -> str:
        return canonical_path(path, root=self.root)

    def canonical_dir(self, path: str | Path) -> str:
        return canonical_path(path, root=self.root)

    def record_file_read(self, path: str | Path) -> str:
        canonical = self.canonical_file(path)
        self.read_files.add(canonical)
        return canonical

    def record_directory_inspection(self, path: str | Path) -> str:
        canonical = self.canonical_dir(path)
        self.inspected_dirs.add(canonical)
        return canonical

    def has_read_file(self, path: str | Path) -> bool:
        return self.canonical_file(path) in self.read_files

    def has_inspected_directory(self, path: str | Path) -> bool:
        return self.canonical_dir(path) in self.inspected_dirs

    def require_prior_read(self, path: str | Path) -> None:
        if not self.has_read_file(path):
            canonical = self.canonical_file(path)
            raise ToolExecutionError(
                f"Cannot modify {canonical}: read_file or read_many_files must read it first."
            )

    def require_parent_inspection(self, path: str | Path) -> None:
        parent = Path(path).parent
        if not self.has_inspected_directory(parent):
            canonical = canonical_path(parent, root=self.root)
            raise ToolExecutionError(
                f"Cannot create file: list_dir must inspect parent directory {canonical} first."
            )

