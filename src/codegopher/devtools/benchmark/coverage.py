"""Focus-queue coverage analysis for development benchmark runs."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any

from codegopher.devtools.benchmark.prepass import StaticFocusQueue

HIGH_SIGNAL_CATEGORIES = {
    "Routes and entry points",
    "Auth and authorization controls",
    "Query, LDAP, and expression sinks",
    "Outbound fetch and SSRF surfaces",
    "Identifier, token, reference, and display helpers",
    "Rendering and raw HTML sinks",
    "State-changing and privileged sinks",
    "Safe controls and possible decoys",
}
TRACKED_TOOL_NAMES = {"read_file", "grep_search", "glob_search", "list_dir"}


@dataclass(frozen=True)
class FocusCategoryCoverage:
    category: str
    total_items: int
    covered_items: int
    covered_paths: tuple[str, ...]
    high_signal: bool

    @property
    def coverage(self) -> float:
        if not self.total_items:
            return 1.0
        return self.covered_items / self.total_items


@dataclass(frozen=True)
class FocusCoverageEvaluation:
    categories: tuple[FocusCategoryCoverage, ...]

    @property
    def total_items(self) -> int:
        return sum(category.total_items for category in self.categories)

    @property
    def covered_items(self) -> int:
        return sum(category.covered_items for category in self.categories)

    @property
    def coverage(self) -> float:
        if not self.total_items:
            return 1.0
        return self.covered_items / self.total_items

    @property
    def high_signal_uncovered_categories(self) -> tuple[str, ...]:
        return tuple(
            category.category
            for category in self.categories
            if category.high_signal and category.total_items and category.covered_items == 0
        )


def evaluate_focus_coverage(
    queue: StaticFocusQueue | None,
    *,
    tool_calls: list[dict[str, Any]],
    report_text: str,
) -> FocusCoverageEvaluation:
    if queue is None:
        return FocusCoverageEvaluation(())
    reviewed_paths = _reviewed_paths(tool_calls=tool_calls, report_text=report_text)
    categories = []
    for category in queue.categories:
        covered_paths = sorted(
            {
                item.path
                for item in category.items
                if _path_was_reviewed(item.path, reviewed_paths, report_text)
            }
        )
        covered_items = sum(
            1
            for item in category.items
            if _path_was_reviewed(item.path, reviewed_paths, report_text)
        )
        categories.append(
            FocusCategoryCoverage(
                category=category.name,
                total_items=len(category.items),
                covered_items=covered_items,
                covered_paths=tuple(covered_paths),
                high_signal=category.name in HIGH_SIGNAL_CATEGORIES,
            )
        )
    return FocusCoverageEvaluation(tuple(categories))


def focus_coverage_to_dict(evaluation: FocusCoverageEvaluation) -> dict[str, Any]:
    return {
        "covered_items": evaluation.covered_items,
        "total_items": evaluation.total_items,
        "coverage": evaluation.coverage,
        "high_signal_uncovered_categories": list(
            evaluation.high_signal_uncovered_categories
        ),
        "categories": [
            {
                "category": category.category,
                "covered_items": category.covered_items,
                "total_items": category.total_items,
                "coverage": category.coverage,
                "covered_paths": list(category.covered_paths),
                "high_signal": category.high_signal,
            }
            for category in evaluation.categories
        ],
    }


def _reviewed_paths(
    *,
    tool_calls: list[dict[str, Any]],
    report_text: str,
) -> set[str]:
    paths = set(_paths_from_text(report_text))
    for call in tool_calls:
        if str(call.get("tool_name", "")) not in TRACKED_TOOL_NAMES:
            continue
        paths.update(_paths_from_text(str(call.get("arguments_summary", ""))))
        payload = _json_payload(str(call.get("arguments_summary", "")))
        paths.update(_paths_from_json(payload))
    return {_normalize_path(path) for path in paths if _normalize_path(path)}


def _path_was_reviewed(path: str, reviewed_paths: set[str], report_text: str) -> bool:
    normalized = _normalize_path(path)
    if not normalized:
        return False
    if normalized in reviewed_paths:
        return True
    parent_parts = PurePosixPath(normalized).parts[:-1]
    prefixes = {
        "/".join(parent_parts[:index])
        for index in range(1, len(parent_parts) + 1)
    }
    if prefixes & reviewed_paths:
        return True
    return normalized.lower() in report_text.lower()


def _json_payload(value: str) -> Any:
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return None


def _paths_from_json(value: Any) -> set[str]:
    if isinstance(value, str):
        return {_normalize_path(value)}
    if isinstance(value, list):
        return {
            path
            for item in value
            for path in _paths_from_json(item)
            if path
        }
    if isinstance(value, dict):
        paths: set[str] = set()
        for key, item in value.items():
            if key in {
                "path",
                "file",
                "directory",
                "root",
                "cwd",
                "pattern",
                "glob",
            } or isinstance(item, (dict, list)):
                paths.update(_paths_from_json(item))
        return {path for path in paths if path}
    return set()


def _paths_from_text(value: str) -> set[str]:
    return {
        _normalize_path(match.group(0))
        for match in re.finditer(
            r"[\w./\\-]+\.(?:py|ts|tsx|js|jsx|java|html|css|sql|xml|ya?ml)",
            value,
            flags=re.I,
        )
    }


def _normalize_path(value: str) -> str:
    value = value.strip().strip("`\"' ")
    value = value.replace("\\", "/")
    value = re.sub(r":\d+(?:-\d+)?$", "", value)
    if value in {"", ".", "./"}:
        return ""
    while value.startswith("./"):
        value = value[2:]
    return value.strip("/")
