from __future__ import annotations

from pathlib import Path

from codegopher.security.models import (
    AttackChain,
    AttackEdge,
    CodeReference,
    Confidence,
    HopNode,
    RemediationStep,
    SecurityAuditReport,
    Severity,
    SinkNode,
    SourceNode,
)
from codegopher.security.report import (
    DEFAULT_CHAINED_VULNERABILITY_REPORT,
    render_report,
    write_report,
)


def make_report() -> SecurityAuditReport:
    chain = AttackChain(
        id="chain-001",
        title="Redirect to admin token reuse",
        severity=Severity.high,
        confidence=Confidence.medium,
        impact="Account takeover",
        sources=[
            SourceNode(
                id="source",
                label="OAuth callback",
                entry_type="route",
                references=[CodeReference(file_path="app/routes.py", start_line=10)],
            )
        ],
        hops=[HopNode(id="hop", label="Open redirect", weakness_type="redirect")],
        sinks=[
            SinkNode(
                id="sink",
                label="Admin session",
                sink_type="auth",
                impact="Account takeover",
            )
        ],
        edges=[AttackEdge(source_id="source", target_id="hop"), AttackEdge(source_id="hop", target_id="sink")],
        remediation=[RemediationStep(summary="Allow-list redirect targets")],
    )
    return SecurityAuditReport(reviewed_paths=["app/"], chains=[chain])


def test_render_report_includes_summary_graph_and_remediation() -> None:
    rendered = render_report(make_report())

    assert "- Chains found: 1" in rendered
    assert "- Maximum severity: High" in rendered
    assert "```mermaid\nflowchart TD" in rendered
    assert "Allow-list redirect targets" in rendered
    assert "`app/routes.py:10`" in rendered


def test_write_report_uses_default_security_report_path(tmp_path: Path) -> None:
    target = write_report(make_report(), cwd=tmp_path)

    assert target == tmp_path / DEFAULT_CHAINED_VULNERABILITY_REPORT
    assert target.read_text(encoding="utf-8").startswith("# Chained Vulnerabilities Review")
