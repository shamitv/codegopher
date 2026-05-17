from __future__ import annotations

import codegopher
from codegopher.skills import discover_builtin_skills
from codegopher.tui import CodeGopherApp, launch_tui


def test_package_import_exposes_version() -> None:
    assert codegopher.__version__ == "0.1.0"


def test_tui_imports_are_available() -> None:
    assert CodeGopherApp.__name__ == "CodeGopherApp"
    assert callable(launch_tui)


def test_builtin_skill_discovery_import_is_available() -> None:
    assert callable(discover_builtin_skills)
