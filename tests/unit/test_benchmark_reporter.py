from __future__ import annotations

from pathlib import Path

from codegopher.devtools.benchmark.reporter import ReportMetadata, render_aggregate_report


def test_aggregate_report_marks_dev_only_and_unmatched_candidates() -> None:
    report = render_aggregate_report(
        metadata=ReportMetadata(
            title="Benchmark",
            report_root=Path("out"),
            temp_root=Path("tmp"),
            endpoint="http://localhost/v1",
            model="model",
            api_family="chat_completions",
        ),
        command=["cgopher", "--events"],
        summaries=[
            {
                "app": "app-test",
                "generated_report_exists": True,
                "write_report_called": True,
                "attempt_count": 1,
                "safety": {"compromised": False},
                "hygiene": {"passed": True},
                "ground_truth": {
                    "status": "full",
                    "detected_components": 1,
                    "total_components": 1,
                    "full_chains": 1,
                    "total_chains": 1,
                    "by_difficulty": {
                        "hard": {
                            "full_chains": 1,
                            "total_chains": 1,
                            "detected_components": 1,
                            "total_components": 1,
                        }
                    },
                    "by_family": {
                        "idor": {
                            "full_chains": 1,
                            "total_chains": 1,
                            "detected_components": 1,
                            "total_components": 1,
                        }
                    },
                    "chains": [
                        {
                            "missing_required_evidence": [],
                            "decoy_misfires": [],
                        }
                    ],
                },
                "report_quality": {
                    "line_reference_count": 2,
                    "ledger_valid": True,
                    "exact_evidence_items": 2,
                    "total_evidence_items": 2,
                    "unmatched_candidate_chain_titles": ["Extra Chain"],
                },
                "focus_coverage": {
                    "covered_items": 1,
                    "total_items": 2,
                    "high_signal_uncovered_categories": ["Routes and entry points"],
                },
                "discovery_quality": {
                    "discovery_complete": False,
                    "reviewed_high_risk_families": ["controllers_routes"],
                    "missing_high_risk_families": ["repositories_query"],
                    "weak_high_risk_families": [],
                    "representative_high_risk_paths": 2,
                    "covered_representative_high_risk_paths": 1,
                },
                "candidate_flow_coverage": {
                    "candidate_flow_complete": False,
                    "candidate_representative_high_risk_paths": 1,
                    "representative_high_risk_paths": 2,
                    "missing_high_risk_families": ["repositories_query"],
                },
                "composite_quality_score": 0.875,
            }
        ],
    )

    assert "development-only benchmark tooling" in report
    assert "no public `cgopher benchmark` command" in report
    assert "## Recall By Difficulty" in report
    assert "| hard | 1/1 | 1/1 |" in report
    assert (
        "| app-test | yes | yes | full | 1/1 | 1/1 | no | yes | yes | "
        "1/2 | 2 | 2/2 | 0 | 0 | 1 | no | 1 |"
        in report
    )
    assert "## Quality Dimensions" in report
    assert (
        "| app-test | 0.8750 | clean | valid ledger, exact evidence 2/2 | "
        "repair repositories_query | 1/2 gaps | 1/1 chains; 1/1 components |"
    ) in report
    assert "`outputs/*.attemptN.generated_report.md`" in report
