"""Coordinator scaffolding for chained vulnerability scans."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ScanTarget(BaseModel):
    name: str = Field(min_length=1)
    purpose: str = Field(min_length=1)
    paths: list[str] = Field(default_factory=list)


class ScanPlan(BaseModel):
    targets: list[ScanTarget] = Field(default_factory=list)


def build_scan_plan(paths: list[str]) -> ScanPlan:
    buckets: dict[str, ScanTarget] = {
        "routing": ScanTarget(
            name="routing",
            purpose="Find public routes, API endpoints, controllers, webhooks, and request inputs.",
        ),
        "auth": ScanTarget(
            name="auth",
            purpose="Find authentication, session, authorization, tenant, role, and CSRF logic.",
        ),
        "data": ScanTarget(
            name="data",
            purpose="Find database, ORM, raw SQL, file-system, process, and administrative sinks.",
        ),
        "config": ScanTarget(
            name="config",
            purpose="Find configuration, dependency, CORS, cookie, header, secret, and debug weaknesses.",
        ),
        "jobs": ScanTarget(
            name="jobs",
            purpose="Find queue consumers, scheduled tasks, background inputs, and async workflow hops.",
        ),
    }
    for path in sorted(paths):
        bucket = _bucket_for_path(path)
        buckets[bucket].paths.append(path)
    return ScanPlan(targets=[target for target in buckets.values() if target.paths])


def weakness_hunter_prompt(target: ScanTarget) -> str:
    return (
        "Perform a static-only chained vulnerability scan for this target.\n"
        f"Target: {target.name}\n"
        f"Purpose: {target.purpose}\n"
        "Return structured JSON with findings of kind source, hop, or sink. "
        "Do not run code, probes, dynamic scanners, or exploit payloads.\n"
        "Paths:\n"
        + "\n".join(f"- {path}" for path in target.paths)
    )


def _bucket_for_path(path: str) -> str:
    lowered = path.lower().replace("\\", "/")
    if any(token in lowered for token in ("route", "controller", "handler", "api", "webhook", "view")):
        return "routing"
    if any(token in lowered for token in ("auth", "session", "permission", "role", "tenant", "csrf")):
        return "auth"
    if any(token in lowered for token in ("model", "migration", "repository", "query", "sql", "db", "admin")):
        return "data"
    if any(token in lowered for token in ("job", "queue", "worker", "task", "consumer")):
        return "jobs"
    return "config"
