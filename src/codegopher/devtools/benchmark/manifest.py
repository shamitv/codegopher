"""Manifest parsing for development-only chained-audit benchmarks."""

from __future__ import annotations

import json
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ChainStepManifest:
    step: int
    owasp_id: str
    description: str
    location: str
    method: str
    severity: str
    cwe: str | None = None
    required_evidence: tuple[str, ...] = ()
    negative_evidence: tuple[str, ...] = ()


@dataclass(frozen=True)
class ChainManifest:
    chain_id: str
    chain_name: str
    attack_scenario: str
    impact: str
    components: tuple[ChainStepManifest, ...]
    difficulty: str = "medium"
    subtlety_tags: tuple[str, ...] = ()
    required_evidence: tuple[str, ...] = ()
    chain_prerequisites: tuple[str, ...] = ()
    negative_evidence: tuple[str, ...] = ()
    vulnerability_family: str = "unspecified"


@dataclass(frozen=True)
class VulnerabilityManifest:
    app_id: str
    app_name: str
    language: str
    framework: str
    chained_attacks: tuple[ChainManifest, ...]
    raw: dict[str, Any]


@dataclass(frozen=True)
class BenchmarkCase:
    key: str
    display_name: str
    source: Path
    manifest: Path


def load_vulnerability_manifest(path: Path) -> VulnerabilityManifest:
    data = _read_json_object(path)
    chains = tuple(_parse_chain(raw_chain) for raw_chain in _list(data, "chained_attacks"))
    return VulnerabilityManifest(
        app_id=_string(data, "app_id"),
        app_name=_string(data, "app_name"),
        language=_string(data, "language"),
        framework=_string(data, "framework"),
        chained_attacks=chains,
        raw=data,
    )


def load_benchmark_suite(path: Path) -> tuple[BenchmarkCase, ...]:
    data = tomllib.loads(path.read_text(encoding="utf-8-sig"))
    apps = data.get("apps")
    if not isinstance(apps, list) or not apps:
        raise ValueError("benchmark suite must contain at least one [[apps]] entry")
    base = path.parent
    return tuple(_parse_case(raw_app, base=base) for raw_app in apps)


def parse_app_spec(value: str) -> BenchmarkCase:
    parts = value.split("|")
    if len(parts) != 4:
        raise ValueError("app specs must use KEY|DISPLAY_NAME|SOURCE_PATH|MANIFEST_PATH")
    key, display_name, source, manifest = parts
    if not key.strip() or not display_name.strip():
        raise ValueError("app spec key and display name must be non-empty")
    return BenchmarkCase(
        key=key.strip(),
        display_name=display_name.strip(),
        source=Path(source.strip()),
        manifest=Path(manifest.strip()),
    )


def _parse_case(raw: object, *, base: Path) -> BenchmarkCase:
    if not isinstance(raw, dict):
        raise ValueError("suite app entries must be tables")
    key = _string(raw, "key")
    display_name = str(raw.get("display_name") or key)
    source = _path(raw, "source", base=base)
    manifest = _path(raw, "manifest", base=base)
    return BenchmarkCase(
        key=key,
        display_name=display_name,
        source=source,
        manifest=manifest,
    )


def _parse_chain(raw: object) -> ChainManifest:
    if not isinstance(raw, dict):
        raise ValueError("chained_attacks entries must be objects")
    components = tuple(_parse_step(component) for component in _list(raw, "components"))
    difficulty = str(raw.get("difficulty") or "medium").strip().lower()
    if difficulty not in {"medium", "hard", "expert"}:
        raise ValueError("chain difficulty must be one of: medium, hard, expert")
    return ChainManifest(
        chain_id=_string(raw, "chain_id"),
        chain_name=_string(raw, "chain_name"),
        attack_scenario=_string(raw, "attack_scenario"),
        impact=_string(raw, "impact"),
        components=components,
        difficulty=difficulty,
        subtlety_tags=_string_tuple(raw, "subtlety_tags"),
        required_evidence=_string_tuple(raw, "required_evidence"),
        chain_prerequisites=_string_tuple(raw, "chain_prerequisites"),
        negative_evidence=_string_tuple(raw, "negative_evidence"),
        vulnerability_family=str(raw.get("vulnerability_family") or _infer_family(raw, components)),
    )


def _parse_step(raw: object) -> ChainStepManifest:
    if not isinstance(raw, dict):
        raise ValueError("chain components must be objects")
    step = raw.get("step")
    if not isinstance(step, int):
        raise ValueError("chain component step must be an integer")
    cwe = raw.get("cwe")
    return ChainStepManifest(
        step=step,
        owasp_id=_string(raw, "owasp_id"),
        description=_string(raw, "description"),
        location=_string(raw, "location"),
        method=_string(raw, "method"),
        severity=_string(raw, "severity"),
        cwe=str(cwe) if cwe is not None else None,
        required_evidence=_string_tuple(raw, "required_evidence"),
        negative_evidence=_string_tuple(raw, "negative_evidence"),
    )


def _read_json_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON manifest {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"manifest {path} must contain a JSON object")
    return value


def _string(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"manifest field {key!r} must be a non-empty string")
    return value


def _list(data: dict[str, Any], key: str) -> list[object]:
    value = data.get(key)
    if not isinstance(value, list):
        raise ValueError(f"manifest field {key!r} must be a list")
    return value


def _string_tuple(data: dict[str, Any], key: str) -> tuple[str, ...]:
    value = data.get(key, [])
    if value is None:
        return ()
    if not isinstance(value, list):
        raise ValueError(f"manifest field {key!r} must be a list")
    result: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"manifest field {key!r} must contain only non-empty strings")
        result.append(item.strip())
    return tuple(result)


def _infer_family(raw: dict[str, Any], components: tuple[ChainStepManifest, ...]) -> str:
    text = " ".join(
        [
            str(raw.get("chain_name", "")),
            str(raw.get("attack_scenario", "")),
            " ".join(component.description for component in components),
            " ".join(component.cwe or "" for component in components),
        ]
    ).lower()
    families = (
        ("ssrf", ("ssrf", "server-side request forgery", "cwe-918")),
        ("idor", ("idor", "ownership", "object reference", "cwe-639")),
        ("injection", ("sql", "nosql", "injection", "cwe-89", "cwe-79", "template")),
        ("auth_session", ("session", "token", "password", "credential", "auth", "login")),
        ("crypto", ("crypto", "hash", "md5", "xor", "encrypt", "cwe-327", "cwe-328")),
        ("deserialization", ("deserialize", "deserialization", "objectinputstream", "cwe-502")),
        ("path_traversal", ("path traversal", "archive", "zip", "file path", "cwe-22")),
        ("state_confusion", ("race", "state", "stale", "cache", "workflow")),
    )
    for family, needles in families:
        if any(needle in text for needle in needles):
            return family
    return "unspecified"


def _path(data: dict[str, Any], key: str, *, base: Path) -> Path:
    value = _string(data, key)
    path = Path(value)
    return path if path.is_absolute() else base / path
