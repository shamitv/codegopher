"""Skills — reusable Markdown instruction files."""

from codegopher.skills.catalog import (
    Skill,
    SkillCatalog,
    SkillDiscovery,
    discover_builtin_skills,
    discover_project_skills,
    discover_skills,
    discover_user_skills,
    parse_skill_file,
)
from codegopher.skills.manager import (
    SkillLoadResult,
    SkillManager,
    extract_skill_mentions,
    format_skill_context,
)

__all__ = [
    "Skill",
    "SkillCatalog",
    "SkillDiscovery",
    "SkillLoadResult",
    "SkillManager",
    "discover_builtin_skills",
    "discover_project_skills",
    "discover_skills",
    "discover_user_skills",
    "extract_skill_mentions",
    "format_skill_context",
    "parse_skill_file",
]
