from __future__ import annotations

from pathlib import Path

from codegopher.config.schema import Settings
from codegopher.skills import (
    SkillManager,
    discover_builtin_skills,
    discover_project_skills,
    discover_skills,
    discover_user_skills,
    extract_skill_mentions,
    parse_skill_file,
)
from codegopher.tools.registry import create_default_registry


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
    settings = Settings.model_validate({"skills": {"builtins_enabled": False}})
    write_skill(tmp_path / ".codegopher" / "skills", "testing", "Testing skill")

    result = discover_skills(cwd=tmp_path, settings=settings)

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
    settings = Settings.model_validate({"skills": {"builtins_enabled": False}})
    write_skill(tmp_path / ".codegopher" / "skills", "project-skill", "Project")
    write_skill(tmp_path / "home" / ".codegopher" / "skills", "user-skill", "User")

    result = discover_skills(cwd=tmp_path, settings=settings, home=tmp_path / "home")

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


def test_discovers_builtin_package_skills() -> None:
    result = discover_builtin_skills(settings=Settings())

    skill = result.catalog.get("codegopher")
    assert result.warnings == ()
    assert skill is not None
    assert skill.source == "builtin"
    assert "CodeGopher's existing safety model" in skill.content


def test_discovers_v0_5_and_v0_7_builtin_skill_packs() -> None:
    result = discover_builtin_skills(settings=Settings())

    assert {
        "repo-domain-docs",
        "repo-tech-docs",
        "crud-owasp-static-audit",
        "chained-vulnerability-static-audit",
    }.issubset({skill.id for skill in result.catalog.list()})

    domain_skill = result.catalog.get("repo-domain-docs")
    tech_skill = result.catalog.get("repo-tech-docs")
    security_skill = result.catalog.get("crud-owasp-static-audit")
    chained_skill = result.catalog.get("chained-vulnerability-static-audit")
    assert domain_skill is not None
    assert tech_skill is not None
    assert security_skill is not None
    assert chained_skill is not None
    assert domain_skill.metadata.name == "Repository Domain Documentation"
    assert "docs/domain/" in domain_skill.content
    assert tech_skill.metadata.name == "Repository Technical Documentation"
    assert "docs/technical/" in tech_skill.content
    assert security_skill.metadata.name == "CRUD OWASP Static Audit"
    assert "OWASP Top 10:2025" in security_skill.content
    assert "docs/security/OWASP_TOP10_2025_REVIEW.md" in security_skill.content
    assert chained_skill.metadata.name == "Chained Vulnerability Static Audit"
    assert "docs/security/CHAINED_VULNERABILITIES_REVIEW.md" in chained_skill.content


def test_crud_owasp_static_audit_skill_keeps_static_only_boundary() -> None:
    result = discover_builtin_skills(settings=Settings())
    skill = result.catalog.get("crud-owasp-static-audit")

    assert skill is not None
    content = skill.content.lower()
    assert "static-only" in content
    assert "do not run live http probing" in content
    assert "dynamic scanners" in content
    assert "exploit payloads" in content
    for active_tool in ("sqlmap", "nmap", "nikto", "ffuf", "hydra", "zap", "burp"):
        assert active_tool not in content


def test_chained_vulnerability_skill_keeps_static_only_boundary() -> None:
    result = discover_builtin_skills(settings=Settings())
    skill = result.catalog.get("chained-vulnerability-static-audit")

    assert skill is not None
    content = skill.content.lower()
    assert "static-only" in content
    assert "attack graph" in content
    assert "do not run live http probes" in content
    assert "dynamic scanners" in content
    assert "exploit payloads" in content


def test_builtin_discovery_can_be_disabled() -> None:
    settings = Settings.model_validate({"skills": {"builtins_enabled": False}})

    result = discover_builtin_skills(settings=settings)

    assert result.catalog.list() == []


def test_project_and_user_skills_take_precedence_over_builtin_skills(
    tmp_path: Path,
) -> None:
    write_skill(tmp_path / ".codegopher" / "skills", "codegopher", "Project")
    write_skill(tmp_path / "home" / ".codegopher" / "skills", "codegopher", "User")

    result = discover_skills(cwd=tmp_path, settings=Settings(), home=tmp_path / "home")

    skill = result.catalog.get("codegopher")
    assert skill is not None
    assert skill.source == "project"
    assert skill.content == "Project"


def test_discover_skills_includes_builtin_skills(tmp_path: Path) -> None:
    result = discover_skills(cwd=tmp_path, settings=Settings(), home=tmp_path / "home")

    assert result.catalog.get("codegopher") is not None
    assert result.catalog.get("repo-domain-docs") is not None
    assert result.catalog.get("repo-tech-docs") is not None
    assert result.catalog.get("crud-owasp-static-audit") is not None


def test_parse_skill_file_uses_parent_directory_as_id(tmp_path: Path) -> None:
    path = write_skill(tmp_path, "python-testing", "Use pytest.")

    skill = parse_skill_file(path, source="project")

    assert skill.id == "python-testing"
    assert skill.metadata.name == "Python Testing"
    assert skill.content == "Use pytest."


def test_parse_skill_file_reads_yaml_front_matter(tmp_path: Path) -> None:
    path = write_skill(
        tmp_path,
        "pytest",
        """---
name: Pytest Workflow
description: Project testing workflow
keywords: [tests, pytest, focused]
---
# Ignored Heading

Prefer focused pytest commands.
""",
    )

    skill = parse_skill_file(path, source="project")

    assert skill.metadata.name == "Pytest Workflow"
    assert skill.metadata.description == "Project testing workflow"
    assert skill.metadata.keywords == ["tests", "pytest", "focused"]
    assert skill.content == "# Ignored Heading\n\nPrefer focused pytest commands."


def test_parse_skill_file_supports_comma_keyword_string(tmp_path: Path) -> None:
    path = write_skill(
        tmp_path,
        "reviews",
        """---
keywords: review, diff, quality
---
# Reviews

Review carefully.
""",
    )

    skill = parse_skill_file(path, source="user")

    assert skill.metadata.name == "Reviews"
    assert skill.metadata.keywords == ["review", "diff", "quality"]


def test_parse_skill_file_supports_block_keyword_list(tmp_path: Path) -> None:
    path = write_skill(
        tmp_path,
        "docs",
        """---
keywords:
  - docs
  - writing
---
Write concise docs.
""",
    )

    skill = parse_skill_file(path, source="builtin")

    assert skill.metadata.keywords == ["docs", "writing"]


def test_parse_skill_file_ignores_unclosed_front_matter(tmp_path: Path) -> None:
    path = write_skill(
        tmp_path,
        "broken",
        """---
name: Broken
# Broken
""",
    )

    skill = parse_skill_file(path, source="project")

    assert skill.metadata.name == "Broken"
    assert skill.content.startswith("---")


def test_extract_skill_mentions_from_prompt() -> None:
    assert extract_skill_mentions("use @skill:pytest and @skill:reviews.") == (
        "pytest",
        "reviews",
    )


def test_skill_manager_loads_explicit_skills(tmp_path: Path) -> None:
    write_skill(tmp_path / ".codegopher" / "skills", "pytest", "Pytest")
    manager = SkillManager(
        discover_project_skills(cwd=tmp_path, settings=Settings()).catalog
    )

    result = manager.load_for_prompt("use @skill:pytest")

    assert [skill.id for skill in result.loaded] == ["pytest"]
    assert result.missing == ()
    assert manager.loaded_ids == ("pytest",)


def test_skill_manager_reports_missing_explicit_skills(tmp_path: Path) -> None:
    manager = SkillManager(
        discover_project_skills(cwd=tmp_path, settings=Settings()).catalog
    )

    result = manager.load_for_prompt("use @skill:missing")

    assert result.loaded == ()
    assert result.missing == ("missing",)


def test_skill_manager_autoloads_keyword_matches(tmp_path: Path) -> None:
    write_skill(
        tmp_path / ".codegopher" / "skills",
        "pytest",
        """---
keywords: pytest, tests
---
Use pytest.
""",
    )
    manager = SkillManager(
        discover_project_skills(cwd=tmp_path, settings=Settings()).catalog
    )

    result = manager.load_for_prompt("please run focused pytest checks")

    assert [skill.id for skill in result.loaded] == ["pytest"]
    assert manager.loaded_ids == ("pytest",)


def test_skill_manager_respects_disabled_autoload(tmp_path: Path) -> None:
    write_skill(
        tmp_path / ".codegopher" / "skills",
        "pytest",
        """---
keywords: pytest
---
Use pytest.
""",
    )
    manager = SkillManager(
        discover_project_skills(cwd=tmp_path, settings=Settings()).catalog,
        autoload=False,
    )

    result = manager.load_for_prompt("please run pytest")

    assert result.loaded == ()
    assert manager.loaded_ids == ()


def test_skill_discovery_does_not_execute_sibling_python_files(tmp_path: Path) -> None:
    skill_root = tmp_path / ".codegopher" / "skills"
    write_skill(skill_root, "unsafe", "Use Markdown only.")
    marker = tmp_path / "executed.txt"
    (skill_root / "unsafe" / "plugin.py").write_text(
        f"from pathlib import Path\nPath({str(marker)!r}).write_text('ran')\n",
        encoding="utf-8",
    )

    result = discover_project_skills(cwd=tmp_path, settings=Settings())

    assert result.catalog.get("unsafe") is not None
    assert not marker.exists()


def test_skill_context_uses_only_skill_markdown(tmp_path: Path) -> None:
    skill_root = tmp_path / ".codegopher" / "skills"
    write_skill(skill_root, "focused", "Only this Markdown should load.")
    (skill_root / "focused" / "notes.txt").write_text(
        "Do not load sibling files.",
        encoding="utf-8",
    )
    manager = SkillManager(discover_project_skills(cwd=tmp_path, settings=Settings()).catalog)

    manager.load("focused")

    context = "\n".join(manager.context_items())
    assert "Only this Markdown should load." in context
    assert "Do not load sibling files." not in context


def test_skills_do_not_register_executable_tools(tmp_path: Path) -> None:
    write_skill(tmp_path / ".codegopher" / "skills", "toolish", "Pretend tool.")
    registry = create_default_registry()
    tool_names_before = [tool.name for tool in registry.list()]

    discover_project_skills(cwd=tmp_path, settings=Settings())

    assert [tool.name for tool in registry.list()] == tool_names_before


def test_malformed_skill_file_reports_warning_without_crashing(tmp_path: Path) -> None:
    path = tmp_path / ".codegopher" / "skills" / "binary" / "SKILL.md"
    path.parent.mkdir(parents=True)
    path.write_bytes(b"\xff\xfe\x00")

    result = discover_project_skills(cwd=tmp_path, settings=Settings())

    assert result.catalog.list() == []
    assert result.warnings
    assert "not a UTF-8 text file" in result.warnings[0]
