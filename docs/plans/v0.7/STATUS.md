# CodeGopher v0.7 Chained Vulnerability Detection Status

Last reviewed: 2026-05-24

## Readiness Summary

- v0.7 implementation is complete locally.
- The original plan review issues have been addressed in the implementation plan:
  - `all` skill-pack behavior now includes the chained vulnerability skill.
  - Sub-agent work is defined as deterministic coordinator/linker scaffolding for v0.7, with production scheduling deferred.
  - Static-only safety is enforced through a filtered per-turn tool registry.
  - TUI and VS Code verification are covered by tests.
- Required local LLM verification targets `LOCAL_OPENAI_COMPATIBLE_ENDPOINT` with model `Qwen/Qwen3.6-35B-A3B`.

---

## Current Repository State

| Area / Milestone | Status | Notes |
|---|---|---|
| Milestone 0: Planning & Product Docs | Complete locally | PLAN, STATUS, TODO, roadmap, and intro are updated for the v0.7 chained-vulnerability goal. |
| Milestone 1: Chained Vulnerability Skill | Complete locally | Built-in skill and skill-pack surfaces are implemented locally. |
| Milestone 2: Static Audit Safety Policy | Complete locally | Chained-audit turns use a filtered registry and dedicated report writer. |
| Milestone 3: Attack Graph And Reporting | Complete locally | Graph models, Mermaid renderer, report writer, coordinator, and linker scaffolding are implemented locally. |
| Milestone 4: UI And IDE Invocation | Complete locally | TUI `/audit --chain` is implemented; VS Code uses natural chat forwarding. |
| Milestone 5: Verification | Complete locally | Targeted tests, full Python suite, lint, typecheck, VS Code gates, and required local-LLM integration passed. |

---

## Verified Facts

- `src/codegopher/skills/builtins/chained-vulnerability-static-audit/SKILL.md` exists.
- `cgopher init --skill-pack chained-vulns` is a planned public interface and is covered by unit tests.
- `security` and `all` skill packs include `chained-vulnerability-static-audit`.
- TUI `/audit --chain` submits a normal prompt containing `@skill:chained-vulnerability-static-audit`.
- The static audit policy allows only read/list/search tools, TODO updates, and `write_chained_vulnerability_report`.
- The local endpoint accepted model aliasing to `Qwen/Qwen3.6-35B-A3B`; `/v1/models` timed out during planning and is not used by tests.

---

## Completed Gates

- `python -m pytest` passed with 627 tests.
- `python -m ruff check src tests` passed.
- `python -m mypy src` passed.
- `npm run compile`, `npm run lint`, and `npm test` passed in `extensions/vscode`.
- `python -m pytest tests/integration/test_real_llm_endpoint.py` passed against the required local endpoint.

## Remaining Gates

- CI and release review.
