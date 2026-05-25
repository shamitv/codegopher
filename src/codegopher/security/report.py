"""Markdown report rendering for chained vulnerability audits."""

from __future__ import annotations

from pathlib import Path

from codegopher.security.mermaid import attack_chain_to_mermaid
from codegopher.security.models import AttackChain, CodeReference, SecurityAuditReport

DEFAULT_CHAINED_VULNERABILITY_REPORT = Path(
    "docs/security/CHAINED_VULNERABILITIES_REVIEW.md"
)


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
