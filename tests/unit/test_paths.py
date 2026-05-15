from __future__ import annotations

from pathlib import Path

from codegopher.utils.paths import canonical_path


def test_canonical_path_resolves_relative_segments(tmp_path: Path) -> None:
    value = canonical_path("src/../README.md", root=tmp_path)

    assert value.lower().endswith(str(Path("README.md")).lower())
    assert str(tmp_path).lower() in value.lower()
