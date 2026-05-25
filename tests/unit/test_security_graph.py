from __future__ import annotations

import pytest
from pydantic import ValidationError

from codegopher.security.models import (
    AttackChain,
    AttackEdge,
    CodeReference,
    Confidence,
    Severity,
    SinkNode,
    SourceNode,
)


def test_attack_chain_validates_edge_node_references() -> None:
    with pytest.raises(ValidationError, match="unknown target node"):
        AttackChain(
            id="chain-1",
            title="Broken graph",
            severity=Severity.high,
            confidence=Confidence.medium,
            impact="Account takeover",
            sources=[SourceNode(id="source", label="Login", entry_type="route")],
            sinks=[
                SinkNode(
                    id="sink",
                    label="Admin panel",
                    sink_type="admin",
                    impact="Privilege escalation",
                )
            ],
            edges=[AttackEdge(source_id="source", target_id="missing")],
        )


def test_code_reference_renders_line_ranges() -> None:
    reference = CodeReference(
        file_path="app/routes.py",
        start_line=12,
        end_line=16,
        symbol="callback",
    )

    assert reference.render() == "`app/routes.py:12-16` `callback`"
