from __future__ import annotations

from pathlib import Path

from tests.fixtures.helpers import copy_project_fixture


def test_copy_project_fixture_creates_temp_copy(tmp_path: Path) -> None:
    copied = copy_project_fixture("basic_python_package", tmp_path)

    assert copied.is_dir()
    assert (copied / "README.md").is_file()
