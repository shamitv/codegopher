"""Workspace hygiene helpers for development-only benchmark runs."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

REMOVED_NAMES = ("README.md", "impl_plan.md", ".vulns", "vulns.json", "scenarios.md")

HINT_PATTERN = re.compile(
    r"(?<![A-Za-z0-9])(?:planted|vulnerabilit(?:y|ies)|vulnerable|owasp|cwe|"
    r"a(?:0[1-9]|10)|decoy|ground\s+truth|sandbox|security\s+analysis|"
    r"visualizer|target\s+a(?:0[1-9]|10)|idor|xss|cross-site\s+scripting|"
    r"cross\s+site\s+scripting|trivially\s+enumerable|prerequisite|"
    r"links\s+that\s+follow|exploit)(?![A-Za-z0-9])",
    re.IGNORECASE,
)

TEXT_EXTENSIONS = {
    ".css",
    ".html",
    ".java",
    ".js",
    ".jsx",
    ".properties",
    ".py",
    ".ts",
    ".tsx",
    ".txt",
    ".yaml",
    ".yml",
}


@dataclass(frozen=True)
class SanitizedLocation:
    path: str
    line: int
    action: str
    snippet: str


@dataclass(frozen=True)
class HygieneReport:
    removed_files: tuple[str, ...]
    sanitized_locations: tuple[SanitizedLocation, ...]
    residual_hints: tuple[SanitizedLocation, ...]

    @property
    def passed(self) -> bool:
        return not self.residual_hints


def is_removed_name(name: str) -> bool:
    return name.lower() in {removed.lower() for removed in REMOVED_NAMES}


def remove_agent_visible_files(workspace: Path) -> tuple[str, ...]:
    removed = []
    for path in sorted(workspace.rglob("*")):
        if path.is_file() and is_removed_name(path.name):
            removed.append(path.relative_to(workspace).as_posix())
            path.unlink()
    return tuple(removed)


def sanitize_workspace_hints(workspace: Path) -> tuple[SanitizedLocation, ...]:
    sanitized: list[SanitizedLocation] = []
    for path in _iter_text_files(workspace):
        original = path.read_text(encoding="utf-8", errors="replace").splitlines()
        rewritten = []
        changed = False
        for line_number, line in enumerate(original, start=1):
            cleaned, action = _sanitize_line(line)
            if action:
                sanitized.append(
                    SanitizedLocation(
                        path=path.relative_to(workspace).as_posix(),
                        line=line_number,
                        action=action,
                        snippet=line.strip()[:220],
                    )
                )
                changed = True
            if cleaned is not None:
                rewritten.append(cleaned)
        if changed:
            path.write_text("\n".join(rewritten) + "\n", encoding="utf-8")
    return tuple(sanitized)


def find_residual_hints(workspace: Path) -> tuple[SanitizedLocation, ...]:
    residuals = []
    for path in _iter_text_files(workspace):
        for line_number, line in enumerate(
            path.read_text(encoding="utf-8", errors="replace").splitlines(),
            start=1,
        ):
            if _sanitize_line(line)[1]:
                residuals.append(
                    SanitizedLocation(
                        path=path.relative_to(workspace).as_posix(),
                        line=line_number,
                        action="residual-hint",
                        snippet=line.strip()[:220],
                    )
                )
    return tuple(residuals)


def run_workspace_hygiene(*, workspace: Path, sanitize_source_hints: bool) -> HygieneReport:
    removed = remove_agent_visible_files(workspace)
    sanitized = (
        sanitize_workspace_hints(workspace) if sanitize_source_hints else ()
    )
    residuals = find_residual_hints(workspace) if sanitize_source_hints else ()
    return HygieneReport(
        removed_files=removed,
        sanitized_locations=sanitized,
        residual_hints=residuals,
    )


def hygiene_to_dict(report: HygieneReport) -> dict[str, object]:
    return {
        "passed": report.passed,
        "removed_files": list(report.removed_files),
        "sanitized_locations": [
            {
                "path": item.path,
                "line": item.line,
                "action": item.action,
                "snippet": item.snippet,
            }
            for item in report.sanitized_locations
        ],
        "residual_hints": [
            {
                "path": item.path,
                "line": item.line,
                "action": item.action,
                "snippet": item.snippet,
            }
            for item in report.residual_hints
        ],
    }


def render_hygiene_report(*, app_key: str, report: HygieneReport) -> str:
    lines = [
        f"# Hygiene - {app_key}",
        "",
        f"- Passed: {'yes' if report.passed else 'no'}",
        f"- Removed evaluator files: {len(report.removed_files)}",
        f"- Sanitized source hints: {len(report.sanitized_locations)}",
        f"- Residual source hints: {len(report.residual_hints)}",
        "",
        "## Removed Evaluator Files",
        "",
    ]
    lines.extend(f"- `{path}`" for path in report.removed_files)
    if not report.removed_files:
        lines.append("- None")
    lines.extend(["", "## Sanitized Source Hints", ""])
    lines.extend(_render_locations(report.sanitized_locations))
    lines.extend(["", "## Residual Source Hints", ""])
    lines.extend(_render_locations(report.residual_hints))
    return "\n".join(lines)


def _sanitize_line(line: str) -> tuple[str | None, str | None]:
    if not HINT_PATTERN.search(line):
        return line, None
    stripped = line.lstrip()
    if _is_comment_only(stripped) or _is_hint_only_text(stripped):
        return None, "removed-line"
    for marker in ("//", "#"):
        index = line.find(marker)
        if index >= 0 and HINT_PATTERN.search(line[index:]):
            return line[:index].rstrip(), "stripped-inline-comment"
    html_index = line.find("<!--")
    if html_index >= 0:
        html_end = line.find("-->", html_index)
        if html_end >= 0 and HINT_PATTERN.search(line[html_index : html_end + 3]):
            return (line[:html_index] + line[html_end + 3 :]).rstrip(), "stripped-html-comment"
    if re.match(r"\s*def\s+test_", line) and HINT_PATTERN.search(line):
        return _rewrite_test_name(line), "rewritten-test-name"
    if "<" in line and ">" in line:
        return None, "removed-visible-hint-line"
    return line, None


def _is_comment_only(stripped: str) -> bool:
    return stripped.startswith(("#", "//", "/*", "*", "<!--", '"""', "'''"))


def _is_hint_only_text(stripped: str) -> bool:
    return bool(
        re.match(
            r"^(?:a(?:0[1-9]|10)|owasp|cwe|vulnerabilit|visualizer|"
            r"security\s+analysis|target\s+a(?:0[1-9]|10)|idor|xss)",
            stripped,
            re.I,
        )
    )


def _rewrite_test_name(line: str) -> str:
    return re.sub(
        r"_?(?:decoy|idor|xss|owasp|cwe|a(?:0[1-9]|10)|vulnerabilit(?:y|ies)|vulnerable|sandbox)",
        "",
        line,
        flags=re.IGNORECASE,
    )


def _iter_text_files(workspace: Path) -> tuple[Path, ...]:
    paths = []
    for path in sorted(workspace.rglob("*")):
        if not path.is_file():
            continue
        if _is_generated_report(path, workspace):
            continue
        if path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        if path.stat().st_size > 1_000_000:
            continue
        paths.append(path)
    return tuple(paths)


def _is_generated_report(path: Path, workspace: Path) -> bool:
    try:
        relative = path.relative_to(workspace).as_posix().lower()
    except ValueError:
        return False
    return relative == "docs/security/chained_vulnerabilities_review.md"


def _render_locations(locations: tuple[SanitizedLocation, ...]) -> list[str]:
    if not locations:
        return ["- None"]
    return [
        f"- `{item.path}:{item.line}` {item.action}: {item.snippet}"
        for item in locations
    ]
