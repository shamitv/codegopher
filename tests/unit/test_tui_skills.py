from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from textual.widgets import Input

from codegopher.config.schema import ModelConfig, Settings
from codegopher.providers.mock import MockProvider
from codegopher.tui import CodeGopherApp
from codegopher.tui.session import TuiSessionStore


def make_settings() -> Settings:
    return Settings(model=ModelConfig(provider="openai", name="test-model"))


def make_store(tmp_path: Path) -> TuiSessionStore:
    return TuiSessionStore(data_home=tmp_path / "data")


def make_app(tmp_path: Path, *, settings: Settings | None = None) -> CodeGopherApp:
    return CodeGopherApp(
        settings=settings or make_settings(),
        cwd=tmp_path,
        provider_factory=lambda _settings: MockProvider([[{"type": "done"}]]),
        session_store=make_store(tmp_path),
    )


def write_skill(root: Path, skill_id: str, content: str) -> None:
    path = root / ".codegopher" / "skills" / skill_id / "SKILL.md"
    path.parent.mkdir(parents=True)
    path.write_text(content, encoding="utf-8")


async def submit(app: CodeGopherApp, pilot: Any, value: str) -> None:
    input_widget = app.query_one("#prompt-input", Input)
    input_widget.focus()
    input_widget.value = value
    await pilot.press("enter")
    await pilot.pause(0.1)


def read_session_json(app: CodeGopherApp) -> dict[str, Any]:
    assert app.session_store is not None
    assert app.session_state is not None
    path = app.session_store.sessions_dir / f"{app.session_state.session_id}.json"
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.mark.asyncio
async def test_skills_command_lists_discovered_skills(tmp_path: Path) -> None:
    write_skill(
        tmp_path,
        "pytest",
        """---
name: Pytest
description: Project tests
keywords: pytest, tests
---
Use pytest.
""",
    )
    app = make_app(tmp_path)

    async with app.run_test() as pilot:
        await submit(app, pilot, "/skills")

    assert app.chat_messages[-1].startswith("Skills:")
    assert "Project (1):" in app.chat_messages[-1]
    assert "- pytest [available] Pytest - Project tests (keywords: pytest, tests)" in (
        app.chat_messages[-1]
    )
    assert "Builtin (4):" in app.chat_messages[-1]
    assert "- repo-domain-docs [available] Repository Domain Documentation" in (
        app.chat_messages[-1]
    )
    assert app.status_message == "Displayed skills"


@pytest.mark.asyncio
async def test_skills_load_command_loads_and_persists_skill(tmp_path: Path) -> None:
    write_skill(tmp_path, "pytest", "# Pytest\n\nUse pytest.")
    app = make_app(tmp_path)

    async with app.run_test() as pilot:
        await submit(app, pilot, "/skills load pytest")

    assert app.chat_messages == ["Skill loaded: pytest (project) Pytest"]
    assert app.skill_manager.loaded_ids == ("pytest",)
    assert read_session_json(app)["loaded_skill_ids"] == ["pytest"]


@pytest.mark.asyncio
async def test_skills_load_command_reports_already_loaded_skill(tmp_path: Path) -> None:
    write_skill(tmp_path, "pytest", "# Pytest\n\nUse pytest.")
    app = make_app(tmp_path)

    async with app.run_test() as pilot:
        await submit(app, pilot, "/skills load pytest")
        await submit(app, pilot, "/skills load pytest")

    assert app.chat_messages[-1] == "Skill already loaded: pytest"
    assert app.status_message == "Skill already loaded"


@pytest.mark.asyncio
async def test_skills_load_command_reports_missing_skill(tmp_path: Path) -> None:
    app = make_app(tmp_path)

    async with app.run_test() as pilot:
        await submit(app, pilot, "/skills load missing")

    assert app.chat_messages == ["Error: Skill not found: missing"]
    assert app.status_message == "Error: Skill not found: missing"


@pytest.mark.parametrize("command", ["/skills show", "/skills load", "/skills load a b"])
@pytest.mark.asyncio
async def test_skills_command_rejects_invalid_usage(
    tmp_path: Path,
    command: str,
) -> None:
    app = make_app(tmp_path)

    async with app.run_test() as pilot:
        await submit(app, pilot, command)

    assert app.chat_messages == ["Error: Usage: /skills [load ID]"]


@pytest.mark.asyncio
async def test_skills_command_honors_disabled_skills(tmp_path: Path) -> None:
    settings = make_settings()
    settings.skills.enabled = False
    app = make_app(tmp_path, settings=settings)

    async with app.run_test() as pilot:
        await submit(app, pilot, "/skills")

    assert app.chat_messages == ["Skills are disabled"]
    assert app.status_message == "Skills disabled"


@pytest.mark.asyncio
async def test_skills_listing_marks_loaded_skills(tmp_path: Path) -> None:
    write_skill(tmp_path, "pytest", "# Pytest\n\nUse pytest.")
    app = make_app(tmp_path)

    async with app.run_test() as pilot:
        await submit(app, pilot, "/skills load pytest")
        await submit(app, pilot, "/skills")

    assert "- pytest [loaded] Pytest" in app.chat_messages[-1]
