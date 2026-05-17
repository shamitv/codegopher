from __future__ import annotations

from pathlib import Path

from codegopher.config.schema import Settings
from codegopher.skills import (
    discover_project_skills,
    discover_skills,
    discover_user_skills,
    parse_skill_file,
)


def write_skill(root: Path, skill_id: str, content: str) -> Path:
    path = root / skill_id / "SKILL.md"
    path.parent.mkdir(parents=True)
    path.write_text(content, encoding="utf-8")
    return path


def test_discovers_project_skills_from_configured_directory(tmp_path: Path) -> None:
    path = write_skill(
        tmp_path / ".codegopher" / "skills",
        "pytest",
        "# Pytest\n\nPrefer focused pytest commands.",
    )

    result = discover_project_skills(cwd=tmp_path, settings=Settings())

    skill = result.catalog.get("pytest")
    assert result.warnings == ()
    assert skill is not None
    assert skill.metadata.id == "pytest"
    assert skill.metadata.name == "Pytest"
    assert skill.metadata.source == "project"
    assert skill.metadata.path == str(path)
    assert skill.content == "# Pytest\n\nPrefer focused pytest commands."


def test_project_discovery_uses_custom_project_dir(tmp_path: Path) -> None:
    settings = Settings.model_validate({"skills": {"project_dir": "docs/skills"}})
    write_skill(tmp_path / "docs" / "skills", "reviews", "Review instructions")

    result = discover_project_skills(cwd=tmp_path, settings=settings)

    assert [skill.id for skill in result.catalog.list()] == ["reviews"]


def test_project_discovery_ignores_missing_directory(tmp_path: Path) -> None:
    result = discover_project_skills(cwd=tmp_path, settings=Settings())

    assert result.catalog.list() == []
    assert result.warnings == ()


def test_project_discovery_honors_disabled_skills(tmp_path: Path) -> None:
    settings = Settings.model_validate({"skills": {"enabled": False}})
    write_skill(tmp_path / ".codegopher" / "skills", "pytest", "content")

    result = discover_project_skills(cwd=tmp_path, settings=settings)

    assert result.catalog.list() == []


def test_discover_skills_includes_project_skills(tmp_path: Path) -> None:
    write_skill(tmp_path / ".codegopher" / "skills", "testing", "Testing skill")

    result = discover_skills(cwd=tmp_path, settings=Settings())

    assert [skill.id for skill in result.catalog.list()] == ["testing"]


def test_discovers_user_skills_from_configured_home(tmp_path: Path) -> None:
    path = write_skill(
        tmp_path / ".codegopher" / "skills",
        "python",
        "# Python\n\nPrefer pathlib.",
    )

    result = discover_user_skills(settings=Settings(), home=tmp_path)

    skill = result.catalog.get("python")
    assert result.warnings == ()
    assert skill is not None
    assert skill.metadata.source == "user"
    assert skill.metadata.path == str(path)
    assert skill.content == "# Python\n\nPrefer pathlib."


def test_user_discovery_uses_custom_user_dir(tmp_path: Path) -> None:
    settings = Settings.model_validate({"skills": {"user_dir": "custom-skills"}})
    write_skill(tmp_path / ".codegopher" / "custom-skills", "docs", "Docs skill")

    result = discover_user_skills(settings=settings, home=tmp_path)

    assert [skill.id for skill in result.catalog.list()] == ["docs"]


def test_discover_skills_includes_user_skills(tmp_path: Path) -> None:
    write_skill(tmp_path / ".codegopher" / "skills", "project-skill", "Project")
    write_skill(tmp_path / "home" / ".codegopher" / "skills", "user-skill", "User")

    result = discover_skills(cwd=tmp_path, settings=Settings(), home=tmp_path / "home")

    assert {skill.id for skill in result.catalog.list()} == {
        "project-skill",
        "user-skill",
    }


def test_project_skills_take_precedence_over_user_skills(tmp_path: Path) -> None:
    write_skill(tmp_path / ".codegopher" / "skills", "shared", "Project")
    write_skill(tmp_path / "home" / ".codegopher" / "skills", "shared", "User")

    result = discover_skills(cwd=tmp_path, settings=Settings(), home=tmp_path / "home")

    skill = result.catalog.get("shared")
    assert skill is not None
    assert skill.source == "project"
    assert skill.content == "Project"


def test_parse_skill_file_uses_parent_directory_as_id(tmp_path: Path) -> None:
    path = write_skill(tmp_path, "python-testing", "Use pytest.")

    skill = parse_skill_file(path, source="project")

    assert skill.id == "python-testing"
    assert skill.metadata.name == "Python Testing"
    assert skill.content == "Use pytest."
