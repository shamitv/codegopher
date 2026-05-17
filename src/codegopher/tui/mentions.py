"""File mention parsing and expansion for TUI prompts."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from codegopher.tools.base import ToolContext
from codegopher.tools.fs.ignore import IgnoreMatcher

MentionKind = Literal["path", "glob"]

_GLOB_CHARS = frozenset("*?[")


@dataclass(frozen=True)
class MentionToken:
    raw: str
    value: str
    kind: MentionKind


@dataclass(frozen=True)
class MentionedFile:
    path: str
    content: str


@dataclass(frozen=True)
class MentionExpansion:
    original_prompt: str
    prompt: str
    mentions: tuple[MentionToken, ...] = ()
    files: tuple[MentionedFile, ...] = ()
    errors: tuple[str, ...] = ()
    skipped: tuple[str, ...] = ()

    @property
    def has_mentions(self) -> bool:
        return bool(self.mentions)

    @property
    def has_errors(self) -> bool:
        return bool(self.errors)

    def summary(self) -> str:
        if self.errors:
            return "Mention expansion failed:\n" + "\n".join(
                f"- {error}" for error in self.errors
            )
        if not self.files:
            return "Mention expansion: no files expanded"
        paths = ", ".join(file.path for file in self.files)
        return f"Expanded {len(self.files)} file mention(s): {paths}"


def parse_mentions(prompt: str) -> tuple[MentionToken, ...]:
    """Parse whitespace-delimited @path, @glob:pattern, and glob-like mentions."""
    mentions: list[MentionToken] = []
    for raw_part in prompt.split():
        if not raw_part.startswith("@") or raw_part == "@":
            continue
        value = raw_part[1:]
        if value.startswith("skill:"):
            continue
        if value.startswith("glob:"):
            mentions.append(MentionToken(raw=raw_part, value=value[5:], kind="glob"))
        elif any(char in value for char in _GLOB_CHARS):
            mentions.append(MentionToken(raw=raw_part, value=value, kind="glob"))
        else:
            mentions.append(MentionToken(raw=raw_part, value=value, kind="path"))
    return tuple(mentions)


def expand_mentions(
    prompt: str,
    *,
    cwd: Path,
    tool_context: ToolContext,
    ignore_file: str = ".codegopherignore",
    max_glob_files: int = 20,
) -> MentionExpansion:
    mentions = parse_mentions(prompt)
    if not mentions:
        return MentionExpansion(original_prompt=prompt, prompt=prompt)

    cwd_resolved = cwd.resolve()
    matcher = IgnoreMatcher.from_file(cwd, ignore_file=ignore_file)
    state = _MentionState(
        cwd=cwd,
        cwd_resolved=cwd_resolved,
        matcher=matcher,
        tool_context=tool_context,
        max_glob_files=max_glob_files,
    )

    for mention in mentions:
        if mention.kind == "path":
            state.add_path_mention(mention)
        else:
            state.add_glob_mention(mention)

    files = tuple(state.files)
    errors = tuple(state.errors)
    expanded_prompt = prompt if errors else _build_expanded_prompt(prompt, files)
    return MentionExpansion(
        original_prompt=prompt,
        prompt=expanded_prompt,
        mentions=mentions,
        files=files,
        errors=errors,
        skipped=tuple(state.skipped),
    )


@dataclass
class _MentionState:
    cwd: Path
    cwd_resolved: Path
    matcher: IgnoreMatcher
    tool_context: ToolContext
    max_glob_files: int
    files: list[MentionedFile] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    seen: set[Path] = field(default_factory=set)

    def add_path_mention(self, mention: MentionToken) -> None:
        if not mention.value:
            self.errors.append(f"{mention.raw}: missing path")
            return
        target = Path(mention.value)
        path = target if target.is_absolute() else self.cwd / target
        self._read_file(path, mention.raw)

    def add_glob_mention(self, mention: MentionToken) -> None:
        if not mention.value:
            self.errors.append(f"{mention.raw}: missing glob pattern")
            return
        matches = sorted(self.cwd.glob(mention.value))
        read_count = 0
        outside_count = 0
        ignored_count = 0
        for path in matches:
            resolved = path.resolve(strict=False)
            if not resolved.is_relative_to(self.cwd_resolved):
                outside_count += 1
                continue
            if self.matcher.matches(resolved, self.cwd_resolved):
                ignored_count += 1
                continue
            if not resolved.is_file():
                continue
            if read_count >= self.max_glob_files:
                self.skipped.append(
                    f"{mention.raw}: additional matches skipped after {self.max_glob_files} files"
                )
                break
            if self._read_file(resolved, mention.raw):
                read_count += 1
        if read_count == 0:
            details = []
            if outside_count:
                details.append(f"{outside_count} outside project")
            if ignored_count:
                details.append(f"{ignored_count} ignored")
            suffix = f" ({', '.join(details)})" if details else ""
            self.errors.append(f"{mention.raw}: no matching files{suffix}")

    def _read_file(self, path: Path, raw: str) -> bool:
        resolved = path.resolve(strict=False)
        if not resolved.is_relative_to(self.cwd_resolved):
            self.errors.append(f"{raw}: resolves outside project directory")
            return False
        rel_path = resolved.relative_to(self.cwd_resolved).as_posix()
        if resolved in self.seen:
            return False
        if self.matcher.matches(resolved, self.cwd_resolved):
            self.errors.append(f"{raw}: ignored by .codegopherignore")
            return False
        if not resolved.exists():
            self.errors.append(f"{raw}: file not found")
            return False
        if not resolved.is_file():
            self.errors.append(f"{raw}: not a file")
            return False
        try:
            content = resolved.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            self.errors.append(f"{raw}: not a UTF-8 text file")
            return False
        except OSError as exc:
            self.errors.append(f"{raw}: {exc}")
            return False

        self.seen.add(resolved)
        self.tool_context.access.record_file_read(resolved)
        self.files.append(MentionedFile(path=rel_path, content=content))
        return True


def _build_expanded_prompt(prompt: str, files: tuple[MentionedFile, ...]) -> str:
    if not files:
        return prompt
    sections = [prompt, "", "Mentioned files:"]
    for file in files:
        sections.extend(
            [
                f"## {file.path}",
                "```text",
                file.content.rstrip(),
                "```",
            ]
        )
    return "\n".join(sections)
