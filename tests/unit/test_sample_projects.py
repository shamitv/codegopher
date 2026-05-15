from __future__ import annotations

from pathlib import Path


FIXTURES = Path("tests/fixtures/projects")


def test_basic_python_package_expected_files_exist() -> None:
    root = FIXTURES / "basic_python_package"

    assert (root / "pyproject.toml").is_file()
    assert (root / "src" / "sample_pkg" / "math_utils.py").is_file()
    assert (root / "tests" / "test_math_utils.py").is_file()


def test_buggy_cli_app_expected_files_exist() -> None:
    root = FIXTURES / "buggy_cli_app"

    assert (root / "app.py").is_file()
    assert (root / "tests" / "test_app.py").is_file()


def test_configured_project_expected_files_exist() -> None:
    root = FIXTURES / "configured_project"

    assert (root / ".codegopher" / "settings.toml").is_file()
    assert (root / ".codegopherignore").is_file()
    assert (root / "src" / "visible.txt").is_file()


def test_edit_safety_project_expected_files_exist() -> None:
    root = FIXTURES / "edit_safety_project"

    assert (root / "src" / "existing.py").is_file()
    assert (root / "new_files").is_dir()

