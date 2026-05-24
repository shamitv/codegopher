"""Models for static chained vulnerability attack graphs."""

from __future__ import annotations

from enum import Enum
from typing import Self

from pydantic import BaseModel, Field, model_validator


class Severity(str, Enum):
    informational = "Informational"
    low = "Low"
    medium = "Medium"
    high = "High"
    critical = "Critical"


class Confidence(str, Enum):
    low = "Low"
    medium = "Medium"
    high = "High"


class CodeReference(BaseModel):
    file_path: str = Field(min_length=1)
    start_line: int | None = Field(default=None, ge=1)
    end_line: int | None = Field(default=None, ge=1)
    symbol: str | None = None

    @model_validator(mode="after")
    def validate_line_range(self) -> Self:
        if (
            self.start_line is not None
            and self.end_line is not None
            and self.end_line < self.start_line
        ):
            raise ValueError("end_line must be greater than or equal to start_line")
        return self

    def render(self) -> str:
        suffix = ""
        if self.start_line is not None and self.end_line is not None:
            suffix = f":{self.start_line}-{self.end_line}"
        elif self.start_line is not None:
            suffix = f":{self.start_line}"
        symbol = f" `{self.symbol}`" if self.symbol else ""
        return f"`{self.file_path}{suffix}`{symbol}"


class SourceNode(BaseModel):
    id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    entry_type: str = Field(min_length=1)
    description: str = ""
    references: list[CodeReference] = Field(default_factory=list)


class HopNode(BaseModel):
    id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    weakness_type: str = Field(min_length=1)
    description: str = ""
    references: list[CodeReference] = Field(default_factory=list)


class SinkNode(BaseModel):
    id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    sink_type: str = Field(min_length=1)
    impact: str = Field(min_length=1)
    description: str = ""
    references: list[CodeReference] = Field(default_factory=list)


class AttackEdge(BaseModel):
    source_id: str = Field(min_length=1)
    target_id: str = Field(min_length=1)
    condition: str = ""
    evidence: list[str] = Field(default_factory=list)


class RemediationStep(BaseModel):
    link_id: str | None = None
    summary: str = Field(min_length=1)
    details: str = ""


class AttackChain(BaseModel):
    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    severity: Severity
    confidence: Confidence
    impact: str = Field(min_length=1)
    sources: list[SourceNode] = Field(default_factory=list)
    hops: list[HopNode] = Field(default_factory=list)
    sinks: list[SinkNode] = Field(default_factory=list)
    edges: list[AttackEdge] = Field(default_factory=list)
    prerequisites: list[str] = Field(default_factory=list)
    remediation: list[RemediationStep] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_graph_references(self) -> Self:
        nodes = set[str]()
        nodes.update(node.id for node in self.sources)
        nodes.update(node.id for node in self.hops)
        nodes.update(node.id for node in self.sinks)
        if not nodes:
            raise ValueError("attack chain must contain at least one node")
        for edge in self.edges:
            if edge.source_id not in nodes:
                raise ValueError(f"edge references unknown source node: {edge.source_id}")
            if edge.target_id not in nodes:
                raise ValueError(f"edge references unknown target node: {edge.target_id}")
        return self

    def ordered_nodes(self) -> list[SourceNode | HopNode | SinkNode]:
        return [*self.sources, *self.hops, *self.sinks]


class SecurityAuditReport(BaseModel):
    title: str = "Chained Vulnerabilities Review"
    reviewed_paths: list[str] = Field(default_factory=list)
    methodology: str = "Static-only source review using attack graph chain synthesis."
    chains: list[AttackChain] = Field(default_factory=list)
    unknowns: list[str] = Field(default_factory=list)

    @property
    def max_severity(self) -> Severity | None:
        order = {
            Severity.informational: 0,
            Severity.low: 1,
            Severity.medium: 2,
            Severity.high: 3,
            Severity.critical: 4,
        }
        if not self.chains:
            return None
        return max((chain.severity for chain in self.chains), key=lambda value: order[value])
