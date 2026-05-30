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
    validate_chained_report_text,
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


def test_validate_chained_report_text_accepts_candidate_ledger() -> None:
    content = """# Chained Vulnerabilities Review

## Candidate Chain Ledger

```json
{
  "candidate_chains": [
    {
      "status": "complete",
      "family": "auth",
      "source": [{"path": "app/routes.py", "symbol": "create", "line": 10}],
      "hop": [{"path": "app/service.py", "symbol": "lookup", "line_range": "20-24"}],
      "sink": [{"path": "app/admin.py", "symbol": "delete", "line": 30}],
      "safe_controls": [
        {
          "path": "app/admin.py",
          "symbol": "require_admin",
          "line": 25,
          "classification": "nearby_only"
        }
      ],
      "confidence": "High",
      "missing_evidence": []
    }
  ]
}
```
"""

    assert validate_chained_report_text(content) == []


def test_validate_chained_report_text_rejects_no_chain_without_negative_evidence() -> None:
    content = """# Chained Vulnerabilities Review

No chained vulnerabilities were identified.

## Candidate Chain Ledger

```json
{"candidate_chains":[]}
```
"""

    assert validate_chained_report_text(content) == [
        "no-chain report must include rejected or incomplete candidates with negative evidence"
    ]


def test_validate_chained_report_text_requires_exact_evidence_shape() -> None:
    content = """# Chained Vulnerabilities Review

## Candidate Chain Ledger

```json
{"candidate_chains":[{"status":"complete","family":"auth","source":[{"path":"/tmp/app.py"}],"hop":[],"sink":[],"safe_controls":[],"confidence":"Low","missing_evidence":[]}]}
```
"""

    failures = validate_chained_report_text(content)

    assert "candidate_chains[1].source[1] path must be repository-relative" in failures
    assert "candidate_chains[1].source[1] missing symbol" in failures
    assert "candidate_chains[1].source[1] missing line or line_range" in failures
