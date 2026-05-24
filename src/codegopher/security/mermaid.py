"""Mermaid rendering for chained vulnerability attack graphs."""

from __future__ import annotations

import re

from codegopher.security.models import AttackChain, AttackEdge


def attack_chain_to_mermaid(chain: AttackChain) -> str:
    lines = ["flowchart TD"]
    for node in chain.ordered_nodes():
        node_id = mermaid_id(node.id)
        kind = node.__class__.__name__.replace("Node", "")
        label = escape_label(f"{kind}: {node.label}")
        lines.append(f'    {node_id}["{label}"]')
    for edge in chain.edges:
        label = edge_label(edge)
        lines.append(f"    {mermaid_id(edge.source_id)} -->{label} {mermaid_id(edge.target_id)}")
    return "\n".join(lines)


def mermaid_id(value: str) -> str:
    identifier = re.sub(r"[^A-Za-z0-9_]", "_", value.strip())
    if not identifier:
        return "node"
    if identifier[0].isdigit():
        return f"n_{identifier}"
    return identifier


def escape_label(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def edge_label(edge: AttackEdge) -> str:
    if not edge.condition:
        return ""
    return f'|"{escape_label(edge.condition)}"|'
