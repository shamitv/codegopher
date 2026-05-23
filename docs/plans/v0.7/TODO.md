# CodeGopher v0.7 Chained Vulnerability Detection TODO

This checklist is commit-oriented. Each checkbox represents a single, focused commit. Keep changes small enough that failures can be rolled back safely.

Commit rules:
- Complete, verify, and commit each task before starting the next.
- Include the task ID in the commit message (e.g., `T005 Add chained vulnerability skill definition`).
- Adhere to the static-only boundary.
- Verify using the smallest relevant unit/integration test command.

---

## Milestone 0 - Planning And Setup

- [x] T001: Create `docs/plans/v0.7/PLAN.md` with details of the implementation plan.
  Verify: `test -f docs/plans/v0.7/PLAN.md`
- [x] T002: Create `docs/plans/v0.7/TODO.md` with implementation tasks.
  Verify: `test -f docs/plans/v0.7/TODO.md`
- [x] T003: Create `docs/plans/v0.7/STATUS.md` with initial status and blocker updates.
  Verify: `test -f docs/plans/v0.7/STATUS.md`
- [ ] T004: Update `docs/product/ROADMAP.md` and `docs/product/INTRO.md` to reference the v0.7 chained vulnerability detection goal.
  Verify: `rg -n "chained-vulnerability-static-audit|chained vulnerabilities" docs/product/`

## Milestone 1 - The Chained Vulnerability Skill

- [ ] T005: Create the built-in skill definition file under `src/codegopher/skills/builtins/chained-vulnerability-static-audit/SKILL.md`.
  Verify: `test -f src/codegopher/skills/builtins/chained-vulnerability-static-audit/SKILL.md`
- [ ] T006: Add CLI support for `--skill-pack chained-vulns` and update the `security` pack list in `catalog.py`.
  Verify: `python -m pytest tests/unit/test_cli.py -k test_cli_init_security_skill_pack`
- [ ] T007: Add unit tests verifying discovery, loading, and front-matter metadata parsing for the new skill.
  Verify: `python -m pytest tests/unit/test_skills.py`

## Milestone 2 - Multi-Agent Scan Orchestration

- [ ] T008: Define Python data structures and schemas (Pydantic models) for the Attack Graph: `SourceNode`, `HopNode`, `SinkNode`, and `AttackChain`.
  Verify: `python -m pytest tests/unit/test_security_graph.py`
- [ ] T009: Implement the scan coordinator logic to partition the workspace and assign targets to sub-agents.
  Verify: `python -m pytest tests/unit/test_scan_coordinator.py`
- [ ] T010: Define prompt templates and agent settings for the Weakness Hunter sub-agents.
  Verify: `python -m pytest tests/unit/test_weakness_hunter.py`
- [ ] T011: Define prompt templates and agent settings for the Chain-Linker sub-agent to assemble vulnerability graphs.
  Verify: `python -m pytest tests/unit/test_chain_linker.py`

## Milestone 3 - Reporting & Visualizations

- [ ] T012: Implement a Mermaid.js flowchart generator to draw attack chains dynamically from parsed models.
  Verify: `python -m pytest tests/unit/test_mermaid_generator.py`
- [ ] T013: Implement the report writer to generate the `docs/security/CHAINED_VULNERABILITIES_REVIEW.md` file.
  Verify: `python -m pytest tests/unit/test_report_writer.py`

## Milestone 4 - Integration and Safety Verification

- [ ] T014: Add mock repository fixtures containing vulnerable chains (e.g., path traversal + exposed settings).
  Verify: Check presence of mock files in `tests/fixtures/security/`
- [ ] T015: Run integration tests proving CodeGopher successfully discovers the chain in the fixtures and outputs a valid Mermaid diagram.
  Verify: `python -m pytest tests/integration/test_chained_vulns_integration.py`
- [ ] T016: Add static safety assertion tests verifying the scan does not perform active network operations and does not generate exploit payloads.
  Verify: `python -m pytest tests/integration/test_chained_vulns_safety.py`
