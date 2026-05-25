from __future__ import annotations

from codegopher.security.mermaid import attack_chain_to_mermaid
from codegopher.security.models import (
    AttackChain,
    AttackEdge,
    Confidence,
    HopNode,
    Severity,
    SinkNode,
    SourceNode,
)


def test_attack_chain_to_mermaid_renders_deterministic_flowchart() -> None:
    chain = AttackChain(
        id="chain-1",
        title="SSRF chain",
        severity=Severity.high,
        confidence=Confidence.medium,
        impact="Admin action",
        sources=[SourceNode(id="source:http", label="Webhook URL", entry_type="webhook")],
        hops=[HopNode(id="hop:ssrf", label='Unvalidated "fetch"', weakness_type="SSRF")],
        sinks=[
            SinkNode(
                id="sink:admin",
                label="Internal admin",
                sink_type="admin",
                impact="Remote code execution",
            )
        ],
        edges=[
            AttackEdge(
                source_id="source:http",
                target_id="hop:ssrf",
                condition="URL is fetched",
            ),
            AttackEdge(source_id="hop:ssrf", target_id="sink:admin"),
        ],
    )

    assert attack_chain_to_mermaid(chain) == "\n".join(
        [
            "flowchart TD",
            '    source_http["Source: Webhook URL"]',
            '    hop_ssrf["Hop: Unvalidated \\"fetch\\""]',
            '    sink_admin["Sink: Internal admin"]',
            '    source_http -->|"URL is fetched"| hop_ssrf',
            "    hop_ssrf --> sink_admin",
        ]
    )
