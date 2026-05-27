from __future__ import annotations

from codegopher.devtools.benchmark.coverage import (
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
