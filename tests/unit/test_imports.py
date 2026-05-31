from __future__ import annotations

import tomllib
from pathlib import Path

import codegopher
from codegopher.skills import discover_builtin_skills
from codegopher.tui import CodeGopherApp, launch_tui


def test_package_import_exposes_version() -> None:
    pyproject_path = Path(__file__).resolve().parents[2] / "pyproject.toml"
    project = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))["project"]
    assert codegopher.__version__ == project["version"]


def test_tui_imports_are_available() -> None:
    assert CodeGopherApp.__name__ == "CodeGopherApp"
    assert callable(launch_tui)


def test_builtin_skill_discovery_import_is_available() -> None:
    assert callable(discover_builtin_skills)


def test_config_inspection_import_is_available() -> None:
    from codegopher.config.inspection import inspect_effective_config

    assert callable(inspect_effective_config)


def test_events_session_lazy_export_is_available() -> None:
    from codegopher.events import EventsSession

    assert EventsSession.__name__ == "EventsSession"
