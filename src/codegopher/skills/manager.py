"""Progressive skill loading helpers."""

from __future__ import annotations

from dataclasses import dataclass

from codegopher.skills.catalog import Skill, SkillCatalog

_SKILL_MENTION_PREFIX = "@skill:"
_MENTION_TRAILING_PUNCTUATION = ".,;:!?)]}"


@dataclass(frozen=True)
class SkillLoadResult:
    """Result of trying to load one or more skills."""

    loaded: tuple[Skill, ...] = ()
    already_loaded: tuple[str, ...] = ()
    missing: tuple[str, ...] = ()


class SkillManager:
    """Tracks discovered and loaded skills for a session."""

    def __init__(
        self,
        catalog: SkillCatalog,
        *,
        loaded_ids: tuple[str, ...] | list[str] = (),
        autoload: bool = True,
    ) -> None:
        self.catalog = catalog
        self.autoload = autoload
        self._loaded_ids: list[str] = []
        for skill_id in loaded_ids:
            if catalog.get(skill_id) is not None and skill_id not in self._loaded_ids:
                self._loaded_ids.append(skill_id)

    @property
    def loaded_ids(self) -> tuple[str, ...]:
        return tuple(self._loaded_ids)

    def loaded_skills(self) -> list[Skill]:
        return [
            skill
            for skill_id in self._loaded_ids
            if (skill := self.catalog.get(skill_id)) is not None
        ]

    def context_items(self) -> list[str]:
        return [format_skill_context(skill) for skill in self.loaded_skills()]

    def load(self, skill_id: str) -> SkillLoadResult:
        skill = self.catalog.get(skill_id)
        if skill is None:
            return SkillLoadResult(missing=(skill_id,))
        if skill_id in self._loaded_ids:
            return SkillLoadResult(already_loaded=(skill_id,))
        self._loaded_ids.append(skill_id)
        return SkillLoadResult(loaded=(skill,))

    def load_many(self, skill_ids: tuple[str, ...] | list[str]) -> SkillLoadResult:
        loaded: list[Skill] = []
        already_loaded: list[str] = []
        missing: list[str] = []
        for skill_id in _unique(skill_ids):
            result = self.load(skill_id)
            loaded.extend(result.loaded)
            already_loaded.extend(result.already_loaded)
            missing.extend(result.missing)
        return SkillLoadResult(
            loaded=tuple(loaded),
            already_loaded=tuple(already_loaded),
            missing=tuple(missing),
        )

    def load_for_prompt(self, prompt: str) -> SkillLoadResult:
        explicit_result = self.load_many(extract_skill_mentions(prompt))
        keyword_loaded: list[Skill] = []
        if self.autoload:
            for skill in self.catalog.list():
                if skill.id in self._loaded_ids:
                    continue
                if _skill_matches_prompt(skill, prompt):
                    self._loaded_ids.append(skill.id)
                    keyword_loaded.append(skill)
        return SkillLoadResult(
            loaded=(*explicit_result.loaded, *keyword_loaded),
            already_loaded=explicit_result.already_loaded,
            missing=explicit_result.missing,
        )


def extract_skill_mentions(prompt: str) -> tuple[str, ...]:
    """Extract @skill:ID mentions from a prompt."""
    skill_ids: list[str] = []
    for part in prompt.split():
        if not part.startswith(_SKILL_MENTION_PREFIX):
            continue
        skill_id = part[len(_SKILL_MENTION_PREFIX) :].rstrip(
            _MENTION_TRAILING_PUNCTUATION
        )
        if skill_id:
            skill_ids.append(skill_id)
    return tuple(_unique(skill_ids))


def format_skill_context(skill: Skill) -> str:
    """Format a loaded skill for provider context."""
    return (
        f"## {skill.metadata.name} ({skill.source}:{skill.id})\n"
        f"{skill.content}"
    )


def _skill_matches_prompt(skill: Skill, prompt: str) -> bool:
    prompt_value = prompt.lower()
    candidates = [
        skill.id,
        skill.metadata.name,
        *skill.metadata.keywords,
    ]
    return any(candidate.lower() in prompt_value for candidate in candidates if candidate)


def _unique(values: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    unique_values: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        unique_values.append(value)
    return tuple(unique_values)
