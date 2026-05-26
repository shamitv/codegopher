from __future__ import annotations

import json
import sys
from pathlib import Path

from codegopher.devtools.benchmark.harness import BenchmarkConfig, BenchmarkHarness
from codegopher.devtools.benchmark.manifest import BenchmarkCase
from codegopher.security.report import DEFAULT_CHAINED_VULNERABILITY_REPORT


def write_app(root: Path) -> Path:
    app = root / "app"
    app.mkdir()
    (app / "app.py").write_text("def vulnerable(): pass\n", encoding="utf-8")
    (app / "README.md").write_text("ground truth hint\n", encoding="utf-8")
    (app / "impl_plan.md").write_text("plan hint\n", encoding="utf-8")
    (app / ".vulns").write_text(json.dumps(manifest_json()), encoding="utf-8")
    (app / "vulns.json").write_text("{}", encoding="utf-8")
    (app / "scenarios.md").write_text("scenario hint\n", encoding="utf-8")
    nested = app / "docs"
    nested.mkdir()
    (nested / "README.md").write_text("nested hint\n", encoding="utf-8")
    (nested / "vulns.json").write_text("nested hint\n", encoding="utf-8")
    (nested / "scenarios.md").write_text("nested hint\n", encoding="utf-8")
    return app


def manifest_json() -> dict[str, object]:
    return {
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


def write_fake_cgopher(path: Path) -> Path:
    script = path / "fake_cgopher.py"
    script.write_text(
        """
from pathlib import Path
import json

report = "# Report\\n\\n## Candidate Chain Ledger\\n\\n| Status | Source | Hop | Sink | File | Symbol | Line | Confidence | Missing Evidence | Safe Control |\\n|---|---|---|---|---|---|---|---|---|---|\\n| complete | input | none | vulnerable | app.py | vulnerable | app.py:1 | high | none | none |\\n\\n### Known Chain\\nEvidence: app.py:1 vulnerable.\\n"
target = Path("docs/security/CHAINED_VULNERABILITIES_REVIEW.md")
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(report, encoding="utf-8")
events = [
    {"type": "session_started"},
    {"type": "tool_call", "tool_id": "call-1", "tool_name": "read_file", "arguments_summary": "{\\"path\\":\\"app.py\\"}"},
    {"type": "tool_result", "tool_id": "call-1", "is_error": False, "result_summary": "def vulnerable(): pass"},
    {"type": "tool_call", "tool_id": "call-2", "tool_name": "write_chained_vulnerability_report", "arguments_summary": "{\\"content\\":\\"# Report\\"}"},
    {"type": "tool_result", "tool_id": "call-2", "is_error": False, "result_summary": "Wrote docs/security/CHAINED_VULNERABILITIES_REVIEW.md"},
    {"type": "turn_complete", "final_text": "done"},
]
for event in events:
    print(json.dumps(event))
""".strip(),
        encoding="utf-8",
    )
    return script


def write_corrective_fake_cgopher(path: Path) -> Path:
    script = path / "fake_cgopher_corrective.py"
    script.write_text(
        """
from pathlib import Path
import json
import sys

stdin_text = sys.stdin.read()
prompt = " ".join(sys.argv) + "\\n" + stdin_text
if "Continue the same static-only chained vulnerability review" in prompt:
    report = "# Report\\n\\n## Candidate Chain Ledger\\n\\n| Status | Source | Hop | Sink | File | Symbol | Line | Confidence | Missing Evidence | Safe Control |\\n|---|---|---|---|---|---|---|---|---|---|\\n| complete | input | none | vulnerable | app.py | vulnerable | app.py:1 | high | none | none |\\n\\n### Known Chain\\nEvidence: app.py:1 vulnerable.\\n"
else:
    report = "# Report\\n\\nNo complete chains were found.\\n"
target = Path("docs/security/CHAINED_VULNERABILITIES_REVIEW.md")
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(report, encoding="utf-8")
print(json.dumps({"type": "tool_call", "tool_id": "call-1", "tool_name": "write_chained_vulnerability_report", "arguments_summary": "{\\"content\\":\\"# Report\\"}"}))
print(json.dumps({"type": "tool_result", "tool_id": "call-1", "is_error": False, "result_summary": "Wrote docs/security/CHAINED_VULNERABILITIES_REVIEW.md"}))
print(json.dumps({"type": "turn_complete", "final_text": "done"}))
""".strip(),
        encoding="utf-8",
    )
    return script


def test_prepare_workspace_removes_agent_visible_docs(tmp_path: Path) -> None:
    app = write_app(tmp_path)
    case = BenchmarkCase(
        key="app-test",
        display_name="Test App",
        source=app,
        manifest=app / ".vulns",
    )
    harness = BenchmarkHarness(
        BenchmarkConfig(
            cases=(case,),
            output_dir=tmp_path / "out",
            cgopher_command=(sys.executable, "unused.py"),
            model="model",
            base_url="http://localhost/v1",
            temp_root=tmp_path / "tmp",
        )
    )

    workspace = harness.prepare_workspace(case)

    assert (workspace / "app.py").exists()
    assert not (workspace / "README.md").exists()
    assert not (workspace / "impl_plan.md").exists()
    assert not (workspace / ".vulns").exists()
    assert not (workspace / "vulns.json").exists()
    assert not (workspace / "scenarios.md").exists()
    assert not (workspace / "docs" / "README.md").exists()
    assert not (workspace / "docs" / "vulns.json").exists()
    assert not (workspace / "docs" / "scenarios.md").exists()


def test_prepare_workspace_sanitizes_source_hints(tmp_path: Path) -> None:
    app = write_app(tmp_path)
    (app / "app.py").write_text(
        "\n".join(
            [
                "# OWASP A02: benchmark hint",
                "def vulnerable():",
                "    return True  # vulnerable decoy",
            ]
        ),
        encoding="utf-8",
    )
    (app / "index.html").write_text(
        '<div>Security Analysis (A04 & A07)</div>\n<!-- ground truth -->\n',
        encoding="utf-8",
    )
    case = BenchmarkCase(
        key="app-test",
        display_name="Test App",
        source=app,
        manifest=app / ".vulns",
    )
    harness = BenchmarkHarness(
        BenchmarkConfig(
            cases=(case,),
            output_dir=tmp_path / "out",
            cgopher_command=(sys.executable, "unused.py"),
            model="model",
            base_url="http://localhost/v1",
            temp_root=tmp_path / "tmp",
            sanitize_source_hints=True,
        )
    )

    workspace = harness.prepare_workspace(case)

    assert (workspace / "app.py").read_text(encoding="utf-8") == (
        "def vulnerable():\n    return True\n"
    )
    assert (workspace / "index.html").read_text(encoding="utf-8") == "\n"
    hygiene = json.loads(
        (tmp_path / "out/hygiene/app-test.hygiene.json").read_text(encoding="utf-8")
    )
    assert hygiene["passed"] is True
    assert len(hygiene["sanitized_locations"]) == 4


def test_harness_run_creates_expected_artifacts(tmp_path: Path) -> None:
    app = write_app(tmp_path)
    fake = write_fake_cgopher(tmp_path)
    case = BenchmarkCase(
        key="app-test",
        display_name="Test App",
        source=app,
        manifest=app / ".vulns",
    )
    harness = BenchmarkHarness(
        BenchmarkConfig(
            cases=(case,),
            output_dir=tmp_path / "out",
            cgopher_command=(sys.executable, str(fake)),
            model="model",
            base_url="http://localhost/v1",
            replay_reasoning_content=True,
            temp_root=tmp_path / "tmp",
            sanitize_source_hints=True,
        )
    )

    result = harness.run()

    assert result.report_path.exists()
    summary = json.loads((tmp_path / "out/analysis/app-test.summary.json").read_text())
    assert summary["generated_report_exists"] is True
    assert summary["write_report_called"] is True
    assert summary["ground_truth"]["status"] == "full"
    assert summary["safety"]["compromised"] is False
    assert summary["hygiene"]["passed"] is True
    assert (tmp_path / "out/logs/app-test.events.jsonl").exists()
    assert (tmp_path / "out/outputs/app-test.generated_report.md").exists()
    assert (tmp_path / "out/hygiene/app-test.hygiene.md").exists()


def test_harness_runs_corrective_second_pass_for_missing_quality_gates(
    tmp_path: Path,
) -> None:
    app = write_app(tmp_path)
    fake = write_corrective_fake_cgopher(tmp_path)
    case = BenchmarkCase(
        key="app-test",
        display_name="Test App",
        source=app,
        manifest=app / ".vulns",
    )
    harness = BenchmarkHarness(
        BenchmarkConfig(
            cases=(case,),
            output_dir=tmp_path / "out",
            cgopher_command=(sys.executable, str(fake)),
            model="model",
            base_url="http://localhost/v1",
            temp_root=tmp_path / "tmp",
            sanitize_source_hints=True,
        )
    )

    result = harness.run()

    summary = json.loads((tmp_path / "out/analysis/app-test.summary.json").read_text())
    assert result.report_path.exists()
    assert summary["corrective_pass_used"] is True
    assert summary["attempt_count"] == 2
    assert summary["report_quality"]["line_reference_count"] >= 1
    assert (tmp_path / "out/logs/app-test.attempt2.events.jsonl").exists()


def test_corrective_pass_triggers_for_unresolved_completeness_markers(
    tmp_path: Path,
) -> None:
    app = write_app(tmp_path)
    case = BenchmarkCase(
        key="app-test",
        display_name="Test App",
        source=app,
        manifest=app / ".vulns",
    )
    harness = BenchmarkHarness(
        BenchmarkConfig(
            cases=(case,),
            output_dir=tmp_path / "out",
            cgopher_command=(sys.executable, "unused.py"),
            model="model",
            base_url="http://localhost/v1",
            temp_root=tmp_path / "tmp",
        )
    )
    workspace = harness.prepare_workspace(case)
    report_path = workspace / DEFAULT_CHAINED_VULNERABILITY_REPORT
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        "\n".join(
            [
                "# Report",
                "",
                "## Candidate Chain Ledger",
                "",
                "| Status | Source | Hop | Sink | File | Symbol | Line |",
                "|---|---|---|---|---|---|---|",
                "| complete | source | hop | sink | app.py | vulnerable | app.py:1 |",
                "",
                "No audit of token or identifier generator helpers was completed.",
            ]
        ),
        encoding="utf-8",
    )

    assert harness._needs_corrective_pass(workspace) is True


def test_corrective_pass_triggers_for_abbreviated_code_references(
    tmp_path: Path,
) -> None:
    app = write_app(tmp_path)
    case = BenchmarkCase(
        key="app-test",
        display_name="Test App",
        source=app,
        manifest=app / ".vulns",
    )
    harness = BenchmarkHarness(
        BenchmarkConfig(
            cases=(case,),
            output_dir=tmp_path / "out",
            cgopher_command=(sys.executable, "unused.py"),
            model="model",
            base_url="http://localhost/v1",
            temp_root=tmp_path / "tmp",
        )
    )
    workspace = harness.prepare_workspace(case)
    report_path = workspace / DEFAULT_CHAINED_VULNERABILITY_REPORT
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        "\n".join(
            [
                "# Report",
                "",
                "## Candidate Chain Ledger",
                "",
                "| Status | Source | Hop | Sink | File | Symbol | Line |",
                "|---|---|---|---|---|---|---|",
                "| complete | source | hop | sink | app.py | vulnerable | app.py:1 |",
            ]
        ),
        encoding="utf-8",
    )

    assert harness._needs_corrective_pass(workspace) is True
