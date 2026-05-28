"""Markdown report rendering for chained vulnerability audits."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from codegopher.security.mermaid import attack_chain_to_mermaid
from codegopher.security.models import AttackChain, CodeReference, SecurityAuditReport

DEFAULT_CHAINED_VULNERABILITY_REPORT = Path(
    "docs/security/CHAINED_VULNERABILITIES_REVIEW.md"
)

JSON_FENCE_RE = re.compile(r"```json\s*(?P<body>.*?)```", re.IGNORECASE | re.DOTALL)


def render_report(report: SecurityAuditReport) -> str:
    lines = [
        f"# {report.title}",
        "",
        "## Summary",
        "",
        f"- Chains found: {len(report.chains)}",
        f"- Maximum severity: {report.max_severity.value if report.max_severity else 'None'}",
        f"- Reviewed paths: {', '.join(report.reviewed_paths) if report.reviewed_paths else 'Not specified'}",
        "",
        "## Methodology",
        "",
        report.methodology,
        "",
        "Static-only boundary: no live probing, fuzzing, credential attacks, dynamic scanners, exploit payloads, or network tests were used.",
        "",
    ]
    if report.chains:
        lines.extend(["## Attack Chains", ""])
        for chain in report.chains:
            lines.extend(render_chain(chain))
    else:
        lines.extend(["## Attack Chains", "", "No chained vulnerabilities were identified.", ""])
    if report.unknowns:
        lines.extend(["## Unknowns And Not Reviewed", ""])
        lines.extend(f"- {unknown}" for unknown in report.unknowns)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_chain(chain: AttackChain) -> list[str]:
    lines = [
        f"### {chain.title}",
        "",
        f"- Chain ID: `{chain.id}`",
        f"- Severity: {chain.severity.value}",
        f"- Confidence: {chain.confidence.value}",
        f"- Impact: {chain.impact}",
        "",
        "```mermaid",
        attack_chain_to_mermaid(chain),
        "```",
        "",
        "#### Evidence",
        "",
    ]
    for node in chain.ordered_nodes():
        refs = render_references(node.references)
        lines.append(f"- {node.label}: {node.description or 'No additional description.'}{refs}")
    if chain.prerequisites:
        lines.extend(["", "#### Preconditions", ""])
        lines.extend(f"- {item}" for item in chain.prerequisites)
    if chain.remediation:
        lines.extend(["", "#### Remediation", ""])
        lines.extend(
            f"- {step.summary}{(': ' + step.details) if step.details else ''}"
            for step in chain.remediation
        )
    lines.append("")
    return lines


def render_references(references: list[CodeReference]) -> str:
    if not references:
        return ""
    return " References: " + ", ".join(reference.render() for reference in references)


def write_report(
    report: SecurityAuditReport,
    *,
    cwd: Path,
    path: Path = DEFAULT_CHAINED_VULNERABILITY_REPORT,
) -> Path:
    target = path if path.is_absolute() else cwd / path
    resolved = target.resolve()
    if not resolved.is_relative_to(cwd.resolve()):
        raise ValueError(f"Report path resolves outside project directory: {path}")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_report(report), encoding="utf-8")
    return target


def validate_chained_report_text(content: str) -> list[str]:
    """Return report-shape failures for chained-audit mission gates."""

    failures: list[str] = []
    if "candidate chain ledger" not in content.lower():
        failures.append("missing Candidate Chain Ledger section")
    payload = _first_json_candidate_payload(content)
    if payload is None:
        failures.append("missing fenced JSON candidate ledger")
        return failures
    candidate_chains = payload.get("candidate_chains")
    if not isinstance(candidate_chains, list):
        failures.append("JSON candidate ledger must contain candidate_chains array")
        return failures
    if _claims_no_chains(content) and not candidate_chains:
        failures.append(
            "no-chain report must include rejected or incomplete candidates with negative evidence"
        )
    for index, candidate in enumerate(candidate_chains, start=1):
        if not isinstance(candidate, dict):
            failures.append(f"candidate_chains[{index}] must be an object")
            continue
        for key in ("status", "family", "source", "hop", "sink", "safe_controls", "confidence", "missing_evidence"):
            if key not in candidate:
                failures.append(f"candidate_chains[{index}] missing {key}")
        status = str(candidate.get("status", "")).lower()
        if status in {"incomplete", "rejected", "no_chain", "no-chain"} and not candidate.get(
            "missing_evidence"
        ):
            failures.append(
                f"candidate_chains[{index}] must record missing_evidence for {status or 'non-complete'} status"
            )
        for field in ("source", "hop", "sink"):
            for evidence_index, evidence in enumerate(
                _evidence_objects(candidate.get(field)),
                start=1,
            ):
                failures.extend(
                    _validate_evidence_object(
                        evidence,
                        location=f"candidate_chains[{index}].{field}[{evidence_index}]",
                    )
                )
        for evidence_index, evidence in enumerate(
            _evidence_objects(candidate.get("safe_controls")),
            start=1,
        ):
            failures.extend(
                _validate_evidence_object(
                    evidence,
                    location=f"candidate_chains[{index}].safe_controls[{evidence_index}]",
                    require_classification=True,
                )
            )
    return list(dict.fromkeys(failures))


def _first_json_candidate_payload(content: str) -> dict[str, Any] | None:
    for match in JSON_FENCE_RE.finditer(content):
        try:
            value = json.loads(match.group("body"))
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and "candidate_chains" in value:
            return value
    return None


def _claims_no_chains(content: str) -> bool:
    normalized = content.lower()
    return any(
        marker in normalized
        for marker in (
            "no chained vulnerabilities were identified",
            "no chains detected",
            "no complete chains",
            "chain count: 0",
            "complete chains detected: 0",
        )
    )


def _evidence_objects(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, dict):
        if "path" in value or "file_path" in value:
            return [value]
        found: list[dict[str, Any]] = []
        for child in value.values():
            found.extend(_evidence_objects(child))
        return found
    if isinstance(value, list):
        found = []
        for child in value:
            found.extend(_evidence_objects(child))
        return found
    return []


def _validate_evidence_object(
    evidence: dict[str, Any],
    *,
    location: str,
    require_classification: bool = False,
) -> list[str]:
    failures: list[str] = []
    path = evidence.get("path") or evidence.get("file_path")
    if not isinstance(path, str) or not path.strip():
        failures.append(f"{location} missing path")
    elif Path(path).is_absolute() or ".." in Path(path).parts:
        failures.append(f"{location} path must be repository-relative")
    symbol = evidence.get("symbol")
    if not isinstance(symbol, str) or not symbol.strip():
        failures.append(f"{location} missing symbol")
    if "line" not in evidence and "line_range" not in evidence:
        failures.append(f"{location} missing line or line_range")
    if require_classification:
        classification = evidence.get("classification")
        if classification not in {
            "same_path_blocker",
            "nearby_only",
            "not_applicable",
            "unknown",
        }:
            failures.append(f"{location} has invalid safe-control classification")
    return failures
