"""Chain linker scaffolding for static scanner outputs."""

from __future__ import annotations

import json
from typing import Literal

from pydantic import BaseModel, Field

from codegopher.security.models import (
    AttackChain,
    AttackEdge,
    CodeReference,
    Confidence,
    HopNode,
    RemediationStep,
    Severity,
    SinkNode,
    SourceNode,
)

FindingKind = Literal["source", "hop", "sink"]


class ScannerFinding(BaseModel):
    id: str = Field(min_length=1)
    kind: FindingKind
    label: str = Field(min_length=1)
    category: str = Field(min_length=1)
    description: str = ""
    references: list[CodeReference] = Field(default_factory=list)


class ScannerOutput(BaseModel):
    target: str = Field(min_length=1)
    findings: list[ScannerFinding] = Field(default_factory=list)


def parse_scanner_output(raw_json: str) -> ScannerOutput:
    return ScannerOutput.model_validate(json.loads(raw_json))


def chain_linker_prompt(outputs: list[ScannerOutput]) -> str:
    rendered = "\n".join(
        f"- {output.target}: {len(output.findings)} findings" for output in outputs
    )
    return (
        "Link static scanner findings into attack chains. "
        "Only connect findings with source evidence and mark uncertain links as lower confidence. "
        "Return structured JSON attack chains without exploit payloads.\n"
        f"Scanner outputs:\n{rendered}"
    )


def link_findings(outputs: list[ScannerOutput]) -> list[AttackChain]:
    findings = [finding for output in outputs for finding in output.findings]
    sources = [finding for finding in findings if finding.kind == "source"]
    hops = [finding for finding in findings if finding.kind == "hop"]
    sinks = [finding for finding in findings if finding.kind == "sink"]
    if not sources or not hops or not sinks:
        return []

    source = sources[0]
    hop = hops[0]
    sink = sinks[0]
    return [
        AttackChain(
            id="chain-001",
            title=f"{source.label} to {sink.label} via {hop.label}",
            severity=Severity.high,
            confidence=Confidence.medium,
            impact=sink.description or sink.category,
            sources=[
                SourceNode(
                    id=source.id,
                    label=source.label,
                    entry_type=source.category,
                    description=source.description,
                    references=source.references,
                )
            ],
            hops=[
                HopNode(
                    id=hop.id,
                    label=hop.label,
                    weakness_type=hop.category,
                    description=hop.description,
                    references=hop.references,
                )
            ],
            sinks=[
                SinkNode(
                    id=sink.id,
                    label=sink.label,
                    sink_type=sink.category,
                    impact=sink.description or sink.category,
                    description=sink.description,
                    references=sink.references,
                )
            ],
            edges=[
                AttackEdge(source_id=source.id, target_id=hop.id, condition="user-controlled input reaches weakness"),
                AttackEdge(source_id=hop.id, target_id=sink.id, condition="weakness enables sink access"),
            ],
            remediation=[
                RemediationStep(
                    link_id=hop.id,
                    summary=f"Break the chain at {hop.label}",
                    details="Harden validation, authorization, or configuration around this intermediate weakness.",
                )
            ],
        )
    ]
