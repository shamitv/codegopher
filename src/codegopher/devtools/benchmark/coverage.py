"""Focus-queue coverage analysis for development benchmark runs."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any

from codegopher.devtools.benchmark.prepass import (
    HIGH_RISK_SOURCE_FAMILIES,
    SOURCE_FAMILY_LABELS,
    StaticFocusQueue,
)

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
MIN_HIGH_RISK_PATH_COVERAGE = 0.5
MIN_PATHS_FOR_WEAK_COVERAGE = 3
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


@dataclass(frozen=True)
class SourceFamilyCoverage:
    family: str
    label: str
    total_items: int
    covered_items: int
    total_paths: int
    covered_paths: tuple[str, ...]
    high_risk: bool

    @property
    def coverage(self) -> float:
        if not self.total_items:
            return 1.0
        return self.covered_items / self.total_items

    @property
    def path_coverage(self) -> float:
        if not self.total_paths:
            return 1.0
        return len(self.covered_paths) / self.total_paths


@dataclass(frozen=True)
class DiscoveryQualityEvaluation:
    source_families: tuple[SourceFamilyCoverage, ...]

    @property
    def high_risk_families(self) -> tuple[str, ...]:
        return tuple(family.family for family in self.source_families if family.high_risk)

    @property
    def reviewed_high_risk_families(self) -> tuple[str, ...]:
        return tuple(
            family.family
            for family in self.source_families
            if family.high_risk and family.covered_items > 0
        )

    @property
    def missing_high_risk_families(self) -> tuple[str, ...]:
        return tuple(
            family.family
            for family in self.source_families
            if family.high_risk and family.total_items and family.covered_items == 0
        )

    @property
    def weak_high_risk_families(self) -> tuple[str, ...]:
        return tuple(
            family.family
            for family in self.source_families
            if family.high_risk
            and family.family not in self.missing_high_risk_families
            and family.total_paths >= MIN_PATHS_FOR_WEAK_COVERAGE
            and family.path_coverage < MIN_HIGH_RISK_PATH_COVERAGE
        )

    @property
    def representative_high_risk_paths(self) -> int:
        return sum(family.total_paths for family in self.source_families if family.high_risk)

    @property
    def covered_representative_high_risk_paths(self) -> int:
        return sum(len(family.covered_paths) for family in self.source_families if family.high_risk)

    @property
    def discovery_complete(self) -> bool:
        return not self.missing_high_risk_families and not self.weak_high_risk_families


@dataclass(frozen=True)
class CandidateFlowFamilyCoverage:
    family: str
    label: str
    total_paths: int
    candidate_paths: tuple[str, ...]
    complete_paths: tuple[str, ...]
    incomplete_paths: tuple[str, ...]
    rejected_paths: tuple[str, ...]
    high_risk: bool

    @property
    def coverage(self) -> float:
        if not self.total_paths:
            return 1.0
        return len(self.candidate_paths) / self.total_paths


@dataclass(frozen=True)
class CandidateFlowCoverageEvaluation:
    source_families: tuple[CandidateFlowFamilyCoverage, ...]

    @property
    def representative_high_risk_paths(self) -> int:
        return sum(family.total_paths for family in self.source_families if family.high_risk)

    @property
    def candidate_representative_high_risk_paths(self) -> int:
        return sum(
            len(family.candidate_paths)
            for family in self.source_families
            if family.high_risk
        )

    @property
    def coverage(self) -> float:
        if not self.representative_high_risk_paths:
            return 1.0
        return (
            self.candidate_representative_high_risk_paths
            / self.representative_high_risk_paths
        )

    @property
    def represented_high_risk_families(self) -> tuple[str, ...]:
        return tuple(
            family.family
            for family in self.source_families
            if family.high_risk and family.candidate_paths
        )

    @property
    def missing_high_risk_families(self) -> tuple[str, ...]:
        return tuple(
            family.family
            for family in self.source_families
            if family.high_risk and family.total_paths and not family.candidate_paths
        )

    @property
    def candidate_flow_complete(self) -> bool:
        return not self.missing_high_risk_families


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


def evaluate_discovery_quality(
    queue: StaticFocusQueue | None,
    *,
    tool_calls: list[dict[str, Any]],
    report_text: str,
) -> DiscoveryQualityEvaluation:
    if queue is None:
        return DiscoveryQualityEvaluation(())
    del report_text
    reviewed_paths = _reviewed_paths(tool_calls=tool_calls, report_text="")
    family_items: dict[str, list[tuple[str, bool]]] = {}
    for category in queue.categories:
        for item in category.items:
            family = item.source_family or "general"
            reviewed = _path_was_reviewed(item.path, reviewed_paths, "")
            family_items.setdefault(family, []).append((item.path, reviewed))

    families = []
    for family, items in sorted(
        family_items.items(),
        key=lambda item: (
            item[0] not in HIGH_RISK_SOURCE_FAMILIES,
            SOURCE_FAMILY_LABELS.get(item[0], item[0]),
        ),
    ):
        total_paths = {path for path, _reviewed in items}
        covered_paths = sorted({path for path, reviewed in items if reviewed})
        families.append(
            SourceFamilyCoverage(
                family=family,
                label=SOURCE_FAMILY_LABELS.get(family, family),
                total_items=len(items),
                covered_items=sum(1 for _path, reviewed in items if reviewed),
                total_paths=len(total_paths),
                covered_paths=tuple(covered_paths),
                high_risk=family in HIGH_RISK_SOURCE_FAMILIES,
            )
        )
    return DiscoveryQualityEvaluation(tuple(families))


def evaluate_candidate_flow_coverage(
    queue: StaticFocusQueue | None,
    *,
    report_text: str,
) -> CandidateFlowCoverageEvaluation:
    if queue is None:
        return CandidateFlowCoverageEvaluation(())
    paths_by_status = _candidate_flow_paths_by_status(report_text)
    candidate_paths = set().union(*paths_by_status.values()) if paths_by_status else set()
    family_paths: dict[str, set[str]] = {}
    for category in queue.categories:
        for item in category.items:
            family = item.source_family or "general"
            family_paths.setdefault(family, set()).add(item.path)

    families = []
    for family, paths in sorted(
        family_paths.items(),
        key=lambda item: (
            item[0] not in HIGH_RISK_SOURCE_FAMILIES,
            SOURCE_FAMILY_LABELS.get(item[0], item[0]),
        ),
    ):
        covered = sorted(
            path for path in paths if _path_was_reviewed(path, candidate_paths, "")
        )
        complete = sorted(
            path
            for path in paths
            if _path_was_reviewed(path, paths_by_status.get("complete", set()), "")
        )
        incomplete = sorted(
            path
            for path in paths
            if _path_was_reviewed(path, paths_by_status.get("incomplete", set()), "")
        )
        rejected = sorted(
            path
            for path in paths
            if _path_was_reviewed(path, paths_by_status.get("rejected", set()), "")
        )
        families.append(
            CandidateFlowFamilyCoverage(
                family=family,
                label=SOURCE_FAMILY_LABELS.get(family, family),
                total_paths=len(paths),
                candidate_paths=tuple(covered),
                complete_paths=tuple(complete),
                incomplete_paths=tuple(incomplete),
                rejected_paths=tuple(rejected),
                high_risk=family in HIGH_RISK_SOURCE_FAMILIES,
            )
        )
    return CandidateFlowCoverageEvaluation(tuple(families))


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


def discovery_quality_to_dict(evaluation: DiscoveryQualityEvaluation) -> dict[str, Any]:
    return {
        "discovery_complete": evaluation.discovery_complete,
        "high_risk_families": list(evaluation.high_risk_families),
        "reviewed_high_risk_families": list(evaluation.reviewed_high_risk_families),
        "missing_high_risk_families": list(evaluation.missing_high_risk_families),
        "weak_high_risk_families": list(evaluation.weak_high_risk_families),
        "covered_representative_high_risk_paths": (
            evaluation.covered_representative_high_risk_paths
        ),
        "representative_high_risk_paths": evaluation.representative_high_risk_paths,
        "source_families": [
            {
                "family": family.family,
                "label": family.label,
                "total_items": family.total_items,
                "covered_items": family.covered_items,
                "coverage": family.coverage,
                "total_paths": family.total_paths,
                "covered_paths": list(family.covered_paths),
                "path_coverage": family.path_coverage,
                "high_risk": family.high_risk,
            }
            for family in evaluation.source_families
        ],
    }


def candidate_flow_coverage_to_dict(
    evaluation: CandidateFlowCoverageEvaluation,
) -> dict[str, Any]:
    return {
        "candidate_flow_complete": evaluation.candidate_flow_complete,
        "coverage": evaluation.coverage,
        "candidate_representative_high_risk_paths": (
            evaluation.candidate_representative_high_risk_paths
        ),
        "representative_high_risk_paths": evaluation.representative_high_risk_paths,
        "represented_high_risk_families": list(
            evaluation.represented_high_risk_families
        ),
        "missing_high_risk_families": list(evaluation.missing_high_risk_families),
        "source_families": [
            {
                "family": family.family,
                "label": family.label,
                "total_paths": family.total_paths,
                "candidate_paths": list(family.candidate_paths),
                "complete_paths": list(family.complete_paths),
                "incomplete_paths": list(family.incomplete_paths),
                "rejected_paths": list(family.rejected_paths),
                "coverage": family.coverage,
                "high_risk": family.high_risk,
            }
            for family in evaluation.source_families
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


def _candidate_flow_paths_by_status(report_text: str) -> dict[str, set[str]]:
    paths_by_status: dict[str, set[str]] = {
        "complete": set(),
        "incomplete": set(),
        "rejected": set(),
    }
    for block in _json_code_blocks(report_text):
        try:
            value = json.loads(block)
        except json.JSONDecodeError:
            continue
        if not isinstance(value, dict):
            continue
        candidates = value.get("candidate_chains")
        if not isinstance(candidates, list):
            continue
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            status = _candidate_status(candidate)
            if status not in paths_by_status:
                continue
            paths_by_status[status].update(_candidate_source_hop_sink_paths(candidate))
    return paths_by_status


def _json_code_blocks(text: str) -> tuple[str, ...]:
    return tuple(
        match.group(1).strip()
        for match in re.finditer(r"```json\s*(.*?)```", text, flags=re.I | re.S)
    )


def _candidate_status(candidate: dict[str, Any]) -> str:
    raw = str(candidate.get("status", "")).lower().replace("-", "_").replace(" ", "_")
    if "complete" in raw and "incomplete" not in raw:
        return "complete"
    if "reject" in raw or "blocked" in raw or "safe_control" in raw:
        return "rejected"
    if "incomplete" in raw or "missing" in raw or "partial" in raw:
        return "incomplete"
    return raw


def _candidate_source_hop_sink_paths(candidate: dict[str, Any]) -> set[str]:
    paths: set[str] = set()
    for key in ("source", "hop", "sink"):
        paths.update(_paths_from_evidence_value(candidate.get(key)))
    return {path for path in paths if path}


def _paths_from_evidence_value(value: Any) -> set[str]:
    if isinstance(value, str):
        return _paths_from_text(value)
    if isinstance(value, list):
        return {
            path
            for item in value
            for path in _paths_from_evidence_value(item)
            if path
        }
    if isinstance(value, dict):
        paths: set[str] = set()
        for key in ("path", "file", "location"):
            raw = value.get(key)
            if isinstance(raw, str):
                normalized = _normalize_path(raw)
                if normalized:
                    paths.add(normalized)
        nested = value.get("evidence")
        if nested is not None:
            paths.update(_paths_from_evidence_value(nested))
        return paths
    return set()


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
    if "/workspace/" in value:
        value = value.split("/workspace/", 1)[1]
    if value in {"", ".", "./"}:
        return ""
    while value.startswith("./"):
        value = value[2:]
    return value.strip("/")
