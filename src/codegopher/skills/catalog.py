"""Markdown skill discovery and catalog helpers."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from importlib import resources
from pathlib import Path

from codegopher.config.schema import Settings
from codegopher.core.types import SkillMetadata, SkillSource


@dataclass(frozen=True)
class Skill:
    """A read-only Markdown skill loaded from a SKILL.md file."""

    metadata: SkillMetadata
    content: str

    @property
    def id(self) -> str:
        return self.metadata.id

    @property
    def source(self) -> SkillSource:
        return self.metadata.source


@dataclass(frozen=True)
class SkillDiscovery:
    """Skill discovery result plus non-fatal warnings."""

    catalog: "SkillCatalog"
    warnings: tuple[str, ...] = ()


class SkillCatalog:
    """A deterministic skill collection keyed by skill id."""

    def __init__(self, skills: Iterable[Skill] = ()) -> None:
        self._skills: dict[str, Skill] = {}
        for skill in skills:
            self._skills.setdefault(skill.id, skill)

    def get(self, skill_id: str) -> Skill | None:
        return self._skills.get(skill_id)

    def list(self) -> list[Skill]:
        return sorted(self._skills.values(), key=lambda skill: (skill.source, skill.id))

    def by_source(self, source: SkillSource) -> list[Skill]:
        return [skill for skill in self.list() if skill.source == source]


def discover_skills(
    *,
    cwd: Path,
    settings: Settings,
    home: Path | None = None,
) -> SkillDiscovery:
    """Discover configured Markdown skills."""
    if not settings.skills.enabled:
        return SkillDiscovery(catalog=SkillCatalog())

    skills: list[Skill] = []
    warnings: list[str] = []
    project_result = discover_project_skills(cwd=cwd, settings=settings)
    user_result = discover_user_skills(settings=settings, home=home)
    builtin_result = discover_builtin_skills(settings=settings)
    skills.extend(project_result.catalog.list())
    skills.extend(user_result.catalog.list())
    skills.extend(builtin_result.catalog.list())
    warnings.extend(project_result.warnings)
    warnings.extend(user_result.warnings)
    warnings.extend(builtin_result.warnings)
    return SkillDiscovery(catalog=SkillCatalog(skills), warnings=tuple(warnings))


def discover_project_skills(*, cwd: Path, settings: Settings) -> SkillDiscovery:
    """Discover project-local .codegopher/skills/*/SKILL.md files."""
    if not settings.skills.enabled:
        return SkillDiscovery(catalog=SkillCatalog())

    root = cwd / settings.skills.project_dir
    return _discover_skill_dir(root=root, source="project")


def discover_user_skills(
    *,
    settings: Settings,
    home: Path | None = None,
) -> SkillDiscovery:
    """Discover user-level ~/.codegopher/skills/*/SKILL.md files."""
    if not settings.skills.enabled:
        return SkillDiscovery(catalog=SkillCatalog())

    root = (home or Path.home()) / ".codegopher" / settings.skills.user_dir
    return _discover_skill_dir(root=root, source="user")


def discover_builtin_skills(*, settings: Settings) -> SkillDiscovery:
    """Discover packaged built-in SKILL.md files."""
    if not settings.skills.enabled or not settings.skills.builtins_enabled:
        return SkillDiscovery(catalog=SkillCatalog())

    skills: list[Skill] = []
    warnings: list[str] = []
    try:
        root = resources.files("codegopher.skills.builtins")
    except ModuleNotFoundError as exc:
        return SkillDiscovery(catalog=SkillCatalog(), warnings=(str(exc),))

    for child in sorted(root.iterdir(), key=lambda item: item.name):
        skill_file = child / "SKILL.md"
        if not child.is_dir() or not skill_file.is_file():
            continue
        try:
            with resources.as_file(skill_file) as path:
                skills.append(parse_skill_file(path, source="builtin"))
        except OSError as exc:
            warnings.append(f"{skill_file}: {exc}")
        except UnicodeDecodeError:
            warnings.append(f"{skill_file}: not a UTF-8 text file")
    return SkillDiscovery(catalog=SkillCatalog(skills), warnings=tuple(warnings))


def parse_skill_file(path: Path, *, source: SkillSource) -> Skill:
    """Parse a SKILL.md file into a read-only skill."""
    skill_id = path.parent.name
    raw_content = path.read_text(encoding="utf-8")
    metadata_values, content = _split_skill_markdown(raw_content)
    keywords = _parse_keywords(metadata_values.get("keywords", ""))
    name = metadata_values.get("name") or _first_heading(content) or _title_from_id(skill_id)
    metadata = SkillMetadata(
        id=skill_id,
        name=name,
        source=source,
        description=metadata_values.get("description") or None,
        path=str(path),
        keywords=keywords,
    )
    return Skill(metadata=metadata, content=content.strip())


def _discover_skill_dir(*, root: Path, source: SkillSource) -> SkillDiscovery:
    if not root.exists():
        return SkillDiscovery(catalog=SkillCatalog())

    skills: list[Skill] = []
    warnings: list[str] = []
    for path in sorted(root.glob("*/SKILL.md")):
        try:
            skills.append(parse_skill_file(path, source=source))
        except OSError as exc:
            warnings.append(f"{path}: {exc}")
        except UnicodeDecodeError:
            warnings.append(f"{path}: not a UTF-8 text file")
    return SkillDiscovery(catalog=SkillCatalog(skills), warnings=tuple(warnings))


def _title_from_id(skill_id: str) -> str:
    return skill_id.replace("-", " ").replace("_", " ").title()


def _split_skill_markdown(content: str) -> tuple[dict[str, str], str]:
    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, content

    closing_index: int | None = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            closing_index = index
            break
    if closing_index is None:
        return {}, content

    metadata = _parse_front_matter(lines[1:closing_index])
    body = "\n".join(lines[closing_index + 1 :])
    return metadata, body


def _parse_front_matter(lines: list[str]) -> dict[str, str]:
    metadata: dict[str, str] = {}
    index = 0
    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or ":" not in line:
            index += 1
            continue
        key, value = line.split(":", maxsplit=1)
        key = key.strip()
        if key not in {"name", "description", "keywords"}:
            index += 1
            continue
        value = _strip_quotes(value.strip())
        if key == "keywords" and not value:
            block_values: list[str] = []
            index += 1
            while index < len(lines):
                item = lines[index].strip()
                if not item.startswith("- "):
                    break
                block_values.append(_strip_quotes(item[2:].strip()))
                index += 1
            metadata[key] = ", ".join(item for item in block_values if item)
            continue
        metadata[key] = value
        index += 1
    return metadata


def _parse_keywords(value: str) -> list[str]:
    if not value:
        return []
    if value.startswith("[") and value.endswith("]"):
        value = value[1:-1]
    return [
        keyword
        for raw_keyword in value.split(",")
        if (keyword := _strip_quotes(raw_keyword.strip()))
    ]


def _first_heading(content: str) -> str | None:
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip() or None
    return None


def _strip_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value
