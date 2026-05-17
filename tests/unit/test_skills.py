from __future__ import annotations

from pathlib import Path

from codegopher.config.schema import Settings
from codegopher.skills import discover_project_skills, discover_skills, parse_skill_file


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


def test_parse_skill_file_uses_parent_directory_as_id(tmp_path: Path) -> None:
    path = write_skill(tmp_path, "python-testing", "Use pytest.")

    skill = parse_skill_file(path, source="project")

    assert skill.id == "python-testing"
    assert skill.metadata.name == "Python Testing"
    assert skill.content == "Use pytest."
