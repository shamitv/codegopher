# CodeGopher v0.10 TODO - Mission Contracts And Skill-Led Task Ledgers

This checklist is commit-oriented. Keep the feature general, but use chained vulnerability audit as the first strict completion profile.

## Milestone 0 - Planning Docs

- [x] T001: Create `docs/plans/v0.10/PLAN.md`.
- [x] T002: Create `docs/plans/v0.10/TODO.md`.
- [x] T003: Create `docs/plans/v0.10/STATUS.md`.

## Milestone 1 - Core Mission Runtime

- [x] T004: Define `MissionContract` and `TaskLedger` models.
- [x] T005: Add contract profile registry and activation logic.
- [x] T006: Add skill-to-contract mapping for built-in skills.
- [x] T007: Add generic complex-task soft contract profile.
- [x] T008: Add documentation contract profiles for `repo-tech-docs` and `repo-domain-docs`.
- [x] T009: Add static-security contract profile for `crud-owasp-static-audit`.
- [x] T010: Add strict chained-audit contract profile for `chained-vulnerability-static-audit`.

## Milestone 2 - Agent Integration

- [x] T011: Seed stable TODOs from active contracts.
- [x] T012: Inject contract and ledger state into provider context.
- [x] T013: Include contract and ledger state in compaction prompts.
- [x] T014: Track observed tool calls and tool results in the ledger.
- [x] T015: Validate required tool-call and artifact gates before final completion.
- [x] T016: Add corrective continuation when gates fail.
- [x] T017: Add max recovery attempt handling and incomplete-task outcome.

## Milestone 3 - Persistence And Events

- [x] T018: Persist task ledgers in TUI session files.
- [x] T019: Emit task contract lifecycle events.
- [x] T020: Add TUI active-mission status visibility.

## Milestone 4 - Skill Guidance

- [x] T021: Update `repo-tech-docs` skill guidance to use contract-backed coverage TODOs.
- [x] T022: Update `repo-domain-docs` skill guidance to use contract-backed coverage TODOs.
- [x] T023: Update `crud-owasp-static-audit` skill guidance for evidence, no-findings reports, and gate-aware completion.
- [x] T024: Update `chained-vulnerability-static-audit` skill guidance for source-hop-sink evidence, decoy rejection, and report finalization gates.

## Milestone 5 - Tests And Verification

- [x] T025: Add contract activation and ledger unit tests.
- [x] T026: Add doc-skill and security-skill recovery integration tests.
- [x] T027: Add TUI session persistence tests for task ledgers.
- [x] T028: Add events protocol tests for task lifecycle events.
- [x] T029: Run full Python tests.
- [x] T030: Run Ruff.
- [x] T031: Run mypy.
- [x] T032: Re-run focused chained-audit samples for prior misses.
- [x] T033: Update `STATUS.md` with implementation and verification results.
