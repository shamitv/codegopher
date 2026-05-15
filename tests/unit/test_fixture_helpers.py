from __future__ import annotations

from pathlib import Path

from tests.fixtures.helpers import copy_project_fixture


def test_copy_project_fixture_creates_temp_copy(tmp_path: Path) -> None:
    copied = copy_project_fixture("basic_python_package", tmp_path)

    assert copied.is_dir()
    assert (copied / "README.md").is_file()


def test_copied_fixture_is_isolated_from_source(tmp_path: Path) -> None:
    copied = copy_project_fixture("edit_safety_project", tmp_path)

    target = copied / "src" / "existing.py"
    target.write_text("changed in temp copy\n", encoding="utf-8")

    assert "old value" in Path(
        "tests/fixtures/projects/edit_safety_project/src/existing.py"
    ).read_text(encoding="utf-8")
