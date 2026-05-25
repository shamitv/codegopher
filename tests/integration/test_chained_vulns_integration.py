from __future__ import annotations

import shutil
from pathlib import Path

from codegopher.security.coordinator import build_scan_plan
from codegopher.security.linker import ScannerOutput, link_findings
from codegopher.security.models import CodeReference, SecurityAuditReport
from codegopher.security.report import DEFAULT_CHAINED_VULNERABILITY_REPORT, write_report


def test_mock_chained_vulnerability_scan_writes_mermaid_report(tmp_path: Path) -> None:
    fixture = Path("tests/fixtures/security/chained_flask_app")
    shutil.copytree(fixture, tmp_path / "fixture")
    paths = [
        path.relative_to(tmp_path).as_posix()
        for path in sorted((tmp_path / "fixture").rglob("*"))
        if path.is_file()
    ]
    plan = build_scan_plan(paths)
    assert plan.targets

    outputs = [
        ScannerOutput.model_validate(
            {
                "target": "fixture",
                "findings": [
                    {
                        "id": "source-oauth-callback",
                        "kind": "source",
                        "label": "OAuth callback next parameter",
                        "category": "public route",
                        "description": "The callback accepts user-controlled redirect input.",
                        "references": [
                            CodeReference(
                                file_path="fixture/app.py",
                                start_line=6,
                                end_line=8,
                            ).model_dump()
                        ],
                    },
                    {
                        "id": "hop-open-redirect",
                        "kind": "hop",
                        "label": "Open redirect",
                        "category": "redirect validation",
                        "description": "The route redirects to next_url without allow-listing.",
                        "references": [
                            CodeReference(file_path="fixture/app.py", start_line=8).model_dump()
                        ],
                    },
                    {
                        "id": "sink-admin-export",
                        "kind": "sink",
                        "label": "Internal admin export",
                        "category": "admin data export",
                        "description": "Debug token gates access to sensitive configuration output.",
                        "references": [
                            CodeReference(
                                file_path="fixture/app.py",
                                start_line=11,
                                end_line=16,
                            ).model_dump()
                        ],
                    },
                ],
            }
        )
    ]
    chains = link_findings(outputs)
    report = SecurityAuditReport(reviewed_paths=paths, chains=chains)

    target = write_report(report, cwd=tmp_path)

    rendered = target.read_text(encoding="utf-8")
    assert target == tmp_path / DEFAULT_CHAINED_VULNERABILITY_REPORT
    assert "```mermaid" in rendered
    assert "OAuth callback next parameter" in rendered
    assert "Break the chain at Open redirect" in rendered
