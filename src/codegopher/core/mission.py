"""Mission contracts and task ledgers for long-running agent work."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

MissionStatus = Literal["active", "completed", "incomplete"]


class MissionContract(BaseModel):
    """Runtime-owned definition of what a complex agent task must preserve."""

    id: str = Field(min_length=1)
    profile_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    goal: str = Field(min_length=1)
    required_todos: list[str] = Field(default_factory=list)
    required_tool_calls: list[str] = Field(default_factory=list)
    required_artifacts: list[str] = Field(default_factory=list)
    evidence_requirements: list[str] = Field(default_factory=list)
    completion_gates: list[str] = Field(default_factory=list)
    recovery_prompt: str = Field(min_length=1)
    max_recovery_attempts: int = Field(default=2, ge=0)
    strict: bool = False


class TaskLedger(BaseModel):
    """Session-persistable progress and gate state for a mission contract."""

    id: str = Field(min_length=1)
    contract: MissionContract
    status: MissionStatus = "active"
    seeded_todo_sources: list[str] = Field(default_factory=list)
    observed_tool_calls: list[str] = Field(default_factory=list)
    observed_tool_results: list[str] = Field(default_factory=list)
    observed_artifacts: list[str] = Field(default_factory=list)
    gate_failures: list[str] = Field(default_factory=list)
    recovery_attempts: int = 0
    outcome: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @classmethod
    def start(cls, contract: MissionContract) -> TaskLedger:
        return cls(id=f"ledger-{contract.id}", contract=contract)

    def touch(self) -> None:
        self.updated_at = datetime.now(UTC)

    def record_tool_call(self, tool_name: str) -> None:
        if tool_name not in self.observed_tool_calls:
            self.observed_tool_calls.append(tool_name)
        self.touch()

    def record_tool_result(self, tool_call_id: str) -> None:
        if tool_call_id not in self.observed_tool_results:
            self.observed_tool_results.append(tool_call_id)
        self.touch()

    def record_artifact(self, artifact: str) -> None:
        normalized = artifact.replace("\\", "/")
        if normalized not in self.observed_artifacts:
            self.observed_artifacts.append(normalized)
        self.touch()

    def validate_completion(self, cwd: Path) -> list[str]:
        failures: list[str] = []
        for tool_name in self.contract.required_tool_calls:
            if tool_name not in self.observed_tool_calls:
                failures.append(f"required tool was not called: {tool_name}")
        for artifact in self.contract.required_artifacts:
            target = cwd / artifact
            if target.exists():
                self.record_artifact(artifact)
            else:
                failures.append(f"required artifact is missing: {artifact}")
        self.gate_failures = failures
        self.touch()
        return failures

    def can_recover(self) -> bool:
        return self.recovery_attempts < self.contract.max_recovery_attempts

    def build_recovery_prompt(self, failures: list[str]) -> str:
        self.recovery_attempts += 1
        self.gate_failures = list(failures)
        self.touch()
        missing = "\n".join(f"- {failure}" for failure in failures)
        return (
            f"{self.contract.recovery_prompt}\n\n"
            "The active mission contract is not complete yet. Missing gates:\n"
            f"{missing}\n\n"
            "Continue from the current state. Do not restart the whole task. "
            "Complete only the missing gates, then provide the final response."
        )

    def mark_completed(self) -> None:
        self.status = "completed"
        self.outcome = "completed"
        self.gate_failures = []
        self.touch()

    def mark_incomplete(self, failures: list[str]) -> None:
        self.status = "incomplete"
        self.outcome = "recovery exhausted: " + "; ".join(failures)
        self.gate_failures = list(failures)
        self.touch()

    def context_items(self) -> list[str]:
        lines = [
            f"Mission: {self.contract.title}",
            f"Goal: {self.contract.goal}",
            f"Status: {self.status}",
        ]
        if self.contract.required_todos:
            lines.append("Required TODOs:")
            lines.extend(f"- {item}" for item in self.contract.required_todos)
        if self.contract.required_tool_calls:
            observed = ", ".join(self.observed_tool_calls) or "none yet"
            lines.append(
                "Required tool calls: "
                + ", ".join(self.contract.required_tool_calls)
                + f" (observed: {observed})"
            )
        if self.contract.required_artifacts:
            observed_artifacts = ", ".join(self.observed_artifacts) or "none yet"
            lines.append(
                "Required artifacts: "
                + ", ".join(self.contract.required_artifacts)
                + f" (observed: {observed_artifacts})"
            )
        if self.contract.evidence_requirements:
            lines.append("Evidence requirements:")
            lines.extend(f"- {item}" for item in self.contract.evidence_requirements)
        if self.gate_failures:
            lines.append("Unresolved completion gates:")
            lines.extend(f"- {failure}" for failure in self.gate_failures)
        return lines


def select_mission_contract(
    *,
    prompt: str,
    loaded_skill_ids: tuple[str, ...],
) -> MissionContract | None:
    """Return the most specific mission contract for the prompt and loaded skills."""

    for skill_id in loaded_skill_ids:
        profile = _SKILL_PROFILES.get(skill_id)
        if profile is not None:
            return profile
    if _looks_like_complex_task(prompt):
        return _GENERIC_COMPLEX_TASK
    return None


def todo_source(contract: MissionContract, index: int) -> str:
    return f"mission:{contract.id}:{index}"


def _looks_like_complex_task(prompt: str) -> bool:
    normalized = prompt.lower()
    triggers = (
        "please implement this plan",
        "implement this plan",
        "include these steps",
        "to-do list",
        "todo list",
        "acceptance criteria",
        "test plan",
    )
    return any(trigger in normalized for trigger in triggers)


_GENERIC_COMPLEX_TASK = MissionContract(
    id="generic-complex-task",
    profile_id="generic-complex-task",
    title="Complex Task",
    goal="Maintain an explicit plan, execute required steps, verify the result, and report unresolved work.",
    required_todos=[
        "Clarify or infer the requested outcome and constraints.",
        "Break the work into concrete implementation or analysis steps.",
        "Track verification and any skipped checks.",
        "Summarize the final outcome and remaining risks.",
    ],
    evidence_requirements=[
        "Keep open TODOs current as the task changes.",
        "Record skipped or impossible verification explicitly.",
    ],
    recovery_prompt="The task contract requires an explicit completion check before finishing.",
)

_REPO_TECH_DOCS = MissionContract(
    id="repo-tech-docs",
    profile_id="repo-tech-docs",
    title="Repository Technical Documentation",
    goal="Create engineering documentation grounded in repository evidence and explicit coverage notes.",
    required_todos=[
        "Inventory entry points, manifests, configuration, scripts, tests, and deployment files.",
        "Document architecture, modules, ownership boundaries, and data flow.",
        "Document setup, runtime configuration, APIs, jobs, and operational concerns.",
        "Record source references, assumptions, gaps, and unreviewed areas.",
    ],
    evidence_requirements=[
        "Use repository facts over generic framework descriptions.",
        "Mark unreviewed or unknown areas instead of implying full coverage.",
    ],
    recovery_prompt="The repository technical documentation contract still has missing coverage.",
)

_REPO_DOMAIN_DOCS = MissionContract(
    id="repo-domain-docs",
    profile_id="repo-domain-docs",
    title="Repository Domain Documentation",
    goal="Extract business and functional documentation from repository evidence.",
    required_todos=[
        "Inventory product docs, routes, schemas, tests, fixtures, and user-facing strings.",
        "Map actors, capabilities, workflows, entities, and lifecycle states.",
        "Document business rules, invariants, exceptions, glossary terms, and open questions.",
        "Separate confirmed behavior from inference and unknowns.",
    ],
    evidence_requirements=[
        "Prefer product/test language over implementation jargon.",
        "Attach source evidence or test references to important domain claims.",
    ],
    recovery_prompt="The repository domain documentation contract still has missing coverage.",
)

_CRUD_OWASP_STATIC_AUDIT = MissionContract(
    id="crud-owasp-static-audit",
    profile_id="crud-owasp-static-audit",
    title="CRUD OWASP Static Audit",
    goal="Perform a static OWASP Top 10 review with evidence, missing-test notes, and explicit unknowns.",
    required_todos=[
        "Map routes, controllers, auth/session code, authorization checks, queries, uploads, config, and tests.",
        "Review each OWASP Top 10:2025 category against static evidence.",
        "Record file, method, and line evidence for each finding.",
        "Report no-findings, unknowns, and missing tests explicitly.",
    ],
    evidence_requirements=[
        "Tie every finding to source, tests, configuration, or dependency metadata.",
        "Do not present dynamic or exploit evidence as if it came from static review.",
    ],
    recovery_prompt="The static OWASP audit contract still has missing evidence or reporting work.",
)

_CHAINED_VULNERABILITY_AUDIT = MissionContract(
    id="chained-vulnerability-static-audit",
    profile_id="chained-vulnerability-static-audit",
    title="Chained Vulnerability Static Audit",
    goal="Complete a static attack-chain review and write the chained vulnerability report artifact.",
    required_todos=[
        "Map attack surface: routes, handlers, auth/session, config, jobs, uploads, and external calls.",
        "Inventory weaknesses, safe decoys, and source-controlled assumptions.",
        "Synthesize source-hop-sink chains with file, symbol, and line evidence.",
        "Calibrate confidence, remediation, unknowns, and no-chain findings.",
        "Write and self-check docs/security/CHAINED_VULNERABILITIES_REVIEW.md.",
    ],
    required_tool_calls=["write_chained_vulnerability_report"],
    required_artifacts=["docs/security/CHAINED_VULNERABILITIES_REVIEW.md"],
    evidence_requirements=[
        "Every chain link needs file path, line or line range, symbol, and evidence.",
        "Safe decoy evidence must be rejected explicitly when it appears near a vulnerable flow.",
        "If no complete chains are found, still write a no-chains report.",
    ],
    completion_gates=[
        "write_chained_vulnerability_report called",
        "docs/security/CHAINED_VULNERABILITIES_REVIEW.md exists",
    ],
    recovery_prompt=(
        "The chained vulnerability audit is not complete. Static-only boundaries still apply: "
        "do not run shell commands, live probes, dynamic scanners, network tests, or write outside "
        "the dedicated report path."
    ),
    max_recovery_attempts=2,
    strict=True,
)

_SKILL_PROFILES = {
    "repo-tech-docs": _REPO_TECH_DOCS,
    "repo-domain-docs": _REPO_DOMAIN_DOCS,
    "crud-owasp-static-audit": _CRUD_OWASP_STATIC_AUDIT,
    "chained-vulnerability-static-audit": _CHAINED_VULNERABILITY_AUDIT,
}
