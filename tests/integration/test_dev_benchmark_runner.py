from __future__ import annotations

import json
import sys
from pathlib import Path

from codegopher.devtools.benchmark.__main__ import main


def test_dev_benchmark_runner_creates_artifacts_without_public_cli(tmp_path: Path) -> None:
    app = tmp_path / "app"
    app.mkdir()
    (app / "app.py").write_text(
        "# OWASP A01: hint\n" "def vulnerable(): pass  # vulnerable decoy\n",
        encoding="utf-8",
    )
    (app / "scenarios.md").write_text("scenario hint\n", encoding="utf-8")
    (app / "vulns.json").write_text("{}", encoding="utf-8")
    manifest = app / ".vulns"
    manifest.write_text(
        json.dumps(
            {
                "app_id": "app-test",
                "app_name": "Test App",
                "language": "python",
                "framework": "flask",
                "chained_attacks": [
                    {
                        "chain_id": "chain-01",
                        "chain_name": "Known Chain",
                        "attack_scenario": "scenario",
                        "impact": "data_exfiltration",
                        "components": [
                            {
                                "step": 1,
                                "owasp_id": "A01",
                                "description": "vulnerable source",
                                "location": "app.py",
                                "method": "vulnerable",
                                "severity": "high",
                            }
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    fake = tmp_path / "fake_cgopher.py"
    fake.write_text(
        """
from pathlib import Path
import json
target = Path("docs/security/CHAINED_VULNERABILITIES_REVIEW.md")
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text("# Report\\n\\n### Known Chain\\nEvidence: app.py:1 vulnerable.\\n", encoding="utf-8")
print(json.dumps({"type": "tool_call", "tool_id": "call-1", "tool_name": "write_chained_vulnerability_report", "arguments_summary": "{\\"content\\":\\"# Report\\"}"}))
print(json.dumps({"type": "tool_result", "tool_id": "call-1", "is_error": False, "result_summary": "Wrote docs/security/CHAINED_VULNERABILITIES_REVIEW.md"}))
print(json.dumps({"type": "turn_complete", "final_text": "done"}))
""".strip(),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "--app",
            f"app-test|Test App|{app}|{manifest}",
            "--output-dir",
            str(tmp_path / "out"),
            "--cgopher",
            sys.executable,
            "--cgopher-arg",
            str(fake),
            "--model",
            "model",
            "--base-url",
            "http://localhost/v1",
            "--replay-reasoning-content",
            "--sanitize-source-hints",
        ]
    )

    assert exit_code == 0
    assert (tmp_path / "out/REPORT.md").exists()
    assert (tmp_path / "out/logs/app-test.events.jsonl").exists()
    assert (tmp_path / "out/analysis/app-test.summary.json").exists()
    assert (tmp_path / "out/hygiene/app-test.hygiene.json").exists()
