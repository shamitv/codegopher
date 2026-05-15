from __future__ import annotations

from pathlib import Path

from codegopher.utils.paths import canonical_path


def test_canonical_path_resolves_relative_segments(tmp_path: Path) -> None:
    value = canonical_path("src/../README.md", root=tmp_path)

    assert value.lower().endswith(str(Path("README.md")).lower())
    assert str(tmp_path).lower() in value.lower()


def test_canonical_path_normalizes_windows_case(tmp_path: Path) -> None:
    upper = canonical_path("Folder/File.py", root=tmp_path, force_windows=True)
    lower = canonical_path("folder/file.py", root=tmp_path, force_windows=True)

    assert upper == lower
