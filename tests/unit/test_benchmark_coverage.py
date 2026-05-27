from __future__ import annotations

from codegopher.devtools.benchmark.coverage import (
    discovery_quality_to_dict,
    evaluate_discovery_quality,
    evaluate_focus_coverage,
    focus_coverage_to_dict,
)
from codegopher.devtools.benchmark.prepass import (
    FocusQueueCategory,
    InventoryMatch,
    StaticFocusQueue,
)


def queue() -> StaticFocusQueue:
    return StaticFocusQueue(
        categories=(
            FocusQueueCategory(
                "Routes and entry points",
                (
                    InventoryMatch(
                        category="Routes and entry points",
                        item_id="FQ001",
                        path="src/controllers/orders.py",
                        line=10,
                        snippet="route",
                        source_family="controllers_routes",
                        priority=120,
                    ),
                ),
            ),
            FocusQueueCategory(
                "Query, LDAP, and expression sinks",
                (
                    InventoryMatch(
                        category="Query, LDAP, and expression sinks",
                        item_id="FQ002",
                        path="src/repositories/orders.py",
                        line=22,
                        snippet="SELECT",
                        source_family="repositories_query",
                        priority=102,
                    ),
                ),
            ),
        )
    )


def test_focus_coverage_tracks_read_file_and_report_references() -> None:
    coverage = evaluate_focus_coverage(
        queue(),
        tool_calls=[
            {
                "tool_name": "read_file",
                "arguments_summary": '{"path":"src/controllers/orders.py"}',
            }
        ],
        report_text="Evidence later cites src/repositories/orders.py:22.",
    )

    assert coverage.covered_items == 2
    assert coverage.total_items == 2
    assert coverage.coverage == 1.0
    assert coverage.high_signal_uncovered_categories == ()


def test_focus_coverage_reports_uncovered_high_signal_categories() -> None:
    coverage = evaluate_focus_coverage(
        queue(),
        tool_calls=[],
        report_text="",
    )

    assert coverage.covered_items == 0
    assert coverage.high_signal_uncovered_categories == (
        "Routes and entry points",
        "Query, LDAP, and expression sinks",
    )
    assert focus_coverage_to_dict(coverage)["coverage"] == 0.0


def test_discovery_quality_tracks_high_risk_source_families() -> None:
    discovery = evaluate_discovery_quality(
        queue(),
        tool_calls=[
            {
                "tool_name": "read_file",
                "arguments_summary": '{"path":"src/controllers/orders.py"}',
            }
        ],
        report_text="",
    )

    assert discovery.discovery_complete is False
    assert discovery.reviewed_high_risk_families == ("controllers_routes",)
    assert discovery.missing_high_risk_families == ("repositories_query",)
    assert discovery.covered_representative_high_risk_paths == 1
    assert discovery.representative_high_risk_paths == 2
    payload = discovery_quality_to_dict(discovery)
    assert payload["discovery_complete"] is False
    assert payload["missing_high_risk_families"] == ["repositories_query"]


def test_discovery_quality_does_not_count_report_citations_as_review() -> None:
    discovery = evaluate_discovery_quality(
        queue(),
        tool_calls=[],
        report_text="Evidence cites src/controllers/orders.py:10.",
    )

    assert discovery.reviewed_high_risk_families == ()
    assert discovery.missing_high_risk_families == (
        "controllers_routes",
        "repositories_query",
    )


def test_discovery_quality_flags_under_reviewed_large_families() -> None:
    queue = StaticFocusQueue(
        categories=(
            FocusQueueCategory(
                "Auth and authorization controls",
                tuple(
                    InventoryMatch(
                        category="Auth and authorization controls",
                        item_id=f"FQ00{index}",
                        path=f"src/controllers/controller_{index}.py",
                        line=1,
                        snippet="from flask import session",
                        source_family="controllers_routes",
                        priority=120,
                    )
                    for index in range(1, 5)
                ),
            ),
        )
    )

    discovery = evaluate_discovery_quality(
        queue,
        tool_calls=[
            {
                "tool_name": "read_file",
                "arguments_summary": '{"path":"src/controllers/controller_1.py"}',
            }
        ],
        report_text="",
    )

    assert discovery.missing_high_risk_families == ()
    assert discovery.weak_high_risk_families == ("controllers_routes",)
    assert discovery.discovery_complete is False
