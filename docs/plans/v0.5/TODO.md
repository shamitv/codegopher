# CodeGopher v0.5 Fine-Grained TODO

This checklist is intentionally commit-oriented. Each checkbox should normally be one focused commit.

Commit rules:

- Preserve existing `cgopher init` default behavior.
- Keep skills as read-only Markdown context.
- Do not add active security scanning, exploit generation, executable plugins, or new dependencies.
- Reuse existing skill discovery, loading, and provider context injection.
- After every commit, run the smallest relevant verification command listed for that step.

## Milestone 0 - Planning And Roadmap Setup

- [x] T001: Add `docs/plans/v0.4` placeholder docs for Providers And MCP.
  Verify: `test -f docs/plans/v0.4/PLAN.md && test -f docs/plans/v0.4/TODO.md && test -f docs/plans/v0.4/STATUS.md`
- [x] T002: Add `docs/plans/v0.5/PLAN.md` with the skill-pack implementation direction.
  Verify: `test -f docs/plans/v0.5/PLAN.md`
- [x] T003: Add `docs/plans/v0.5/TODO.md` with commit-sized implementation tasks.
  Verify: `test -f docs/plans/v0.5/TODO.md`
- [x] T004: Add `docs/plans/v0.5/STATUS.md` with initial status and blockers.
  Verify: `test -f docs/plans/v0.5/STATUS.md`
- [x] T005: Update roadmap references so v0.5 is the skill-pack release and Advanced Coding Workflows moves later.
  Verify: `rg -n "v0.5|Repository Documentation|v0.7|Advanced Coding Workflows" docs/product/ROADMAP.md`

## Milestone 1 - Built-In Skill Content

- [x] T006: Add `repo-domain-docs` built-in Markdown skill.
  Verify: `python -m pytest tests/unit/test_skills.py`
- [x] T007: Add `repo-tech-docs` built-in Markdown skill.
  Verify: `python -m pytest tests/unit/test_skills.py`
- [x] T008: Add `crud-owasp-static-audit` built-in Markdown skill with OWASP Top 10:2025 coverage.
  Verify: `python -m pytest tests/unit/test_skills.py`
- [x] T009: Add static-only safety assertions for the OWASP skill.
  Verify: `python -m pytest tests/unit/test_skills.py`

## Milestone 2 - Project Init Skill Packs

- [x] T010: Add `cgopher init --skill-pack repo-docs`.
  Verify: `python -m pytest tests/unit/test_cli.py`
- [x] T011: Add `cgopher init --skill-pack security`.
  Verify: `python -m pytest tests/unit/test_cli.py`
- [x] T012: Add `cgopher init --skill-pack all`.
  Verify: `python -m pytest tests/unit/test_cli.py`
- [x] T013: Preserve skip and `--force` overwrite behavior for materialized skill packs.
  Verify: `python -m pytest tests/unit/test_cli.py`
- [x] T014: Prove skill-pack init does not write settings or secrets.
  Verify: `python -m pytest tests/unit/test_cli.py`

## Milestone 3 - Context Integration

- [x] T015: Prove all v0.5 built-in skills discover from the packaged skill catalog.
  Verify: `python -m pytest tests/unit/test_skills.py`
- [x] T016: Prove `@skill:repo-domain-docs` reaches provider context.
  Verify: `python -m pytest tests/integration/test_init_skill_context.py`
- [x] T017: Prove `@skill:repo-tech-docs` reaches provider context.
  Verify: `python -m pytest tests/integration/test_init_skill_context.py`
- [x] T018: Prove `@skill:crud-owasp-static-audit` reaches provider context.
  Verify: `python -m pytest tests/integration/test_init_skill_context.py`

## Milestone 4 - Docs And Release Readiness

- [x] T019: Update README with skill-pack usage.
  Verify: `rg -n "skill-pack|repo-docs|security" README.md`
- [x] T020: Update architecture docs with built-in skill packs and static-only security boundary.
  Verify: `rg -n "skill pack|static-only|OWASP" docs/arch`
- [x] T021: Update release checklist with v0.5 skill-pack smoke tests.
  Verify: `rg -n "skill-pack|OWASP" docs/release/CHECKLIST.md`
- [x] T022: Add implicit project init scope to v0.5 docs.
  Verify: `rg -n "implicit|first use|--no-project-init|project init" docs/plans/v0.5 README.md docs/release/CHECKLIST.md`

## Milestone 5 - Implicit Project Init

- [x] T023: Add a reusable project-init helper that can run silently for implicit init and visibly for `cgopher init`.
  Verify: `python -m pytest tests/unit/test_cli.py`
- [x] T024: Add global `--no-project-init` CLI flag.
  Verify: `python -m pytest tests/unit/test_cli.py`
- [x] T025: Trigger implicit init before headless prompt execution when `.codegopher/` is missing.
  Verify: `python -m pytest tests/unit/test_cli.py`
- [x] T026: Trigger implicit init before TUI launch when `.codegopher/` is missing.
  Verify: `python -m pytest tests/unit/test_cli.py`
- [x] T027: Preserve no-init behavior for existing `.codegopher/`, `--no-project-init`, non-interactive no-prompt errors, and manual `cgopher init`.
  Verify: `python -m pytest tests/unit/test_cli.py`

## Milestone 6 - Final Verification

- [x] T028: Run the complete unit and integration suite.
  Verify: `source .venv/bin/activate && python -m pytest`
- [x] T029: Run lint checks.
  Verify: `source .venv/bin/activate && ruff check src/ tests/`
- [x] T030: Run static type checking.
  Verify: `source .venv/bin/activate && mypy src/`
- [x] T031: Build distribution artifacts.
  Verify: `source .venv/bin/activate && python -m hatch build`
- [x] T032: Run the machine-specific path guard before final commit.
  Verify: run the local machine-specific path guard and confirm no tracked-source matches.
