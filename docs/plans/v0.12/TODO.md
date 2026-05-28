# CodeGopher v0.12 TODO - Evidence-Led Task Memory

This checklist is commit-oriented. Keep improvements general and avoid app-specific hints from validation corpora.

## Milestone 0 - Planning And Docs

- [x] T001: Create `docs/plans/v0.12/PLAN.md`.
- [x] T002: Create `docs/plans/v0.12/TODO.md`.
- [x] T003: Create `docs/plans/v0.12/STATUS.md`.
- [x] T004: Update `docs/arch` for episode memory, richer TODO state, chained-audit gates, provider usage fallback, and proxy safety.

## Milestone 1 - Episodic Runtime State

- [x] T005: Add task-local episode memory separate from persistent `save_memory`.
- [x] T006: Record compact observations for file reads, searches, directory listings, TODO updates, report writes, tool errors, and final decisions.
- [x] T007: Redact endpoint URLs, temp paths, and secret-like assignments from episode summaries.
- [x] T008: Inject episode memory into provider context separately from selected persistent memories.
- [x] T009: Preserve episode memory during manual and automatic compaction.

## Milestone 2 - TODO And Mission Tracking

- [x] T010: Extend TODO status with `blocked` and `cancelled`.
- [x] T011: Add TODO metadata for reason, related files, and evidence references.
- [x] T012: Add model-facing `update_todo` actions for update, block, unblock, and cancel.
- [x] T013: Enforce one in-progress TODO item by default.
- [x] T014: Seed mission TODOs with mission reasons and artifact evidence references.

## Milestone 3 - Skills And Mission Gates

- [x] T015: Update chained-audit skill guidance for working candidate ledgers.
- [x] T016: Add generic source-to-sink pivot recipes without app-specific hints.
- [x] T017: Require negative evidence for incomplete, rejected, and no-chain conclusions.
- [x] T018: Validate chained-audit reports for Candidate Chain Ledger JSON and exact evidence shape.
- [x] T019: Fail mission completion when required chained-audit report gates are missing.

## Milestone 4 - Safety, Provider, And Benchmark Hardening

- [x] T020: Add static-audit tool-layer denial for hidden evaluator metadata and dotfile paths.
- [x] T021: Add static-audit denial for parent traversal and answer-key terminology searches.
- [x] T022: Add Chat Completions streaming usage options with compatibility fallback.
- [x] T023: Ignore usage-only stream chunks in the runtime event stream.
- [x] T024: Fail fast when proxy benchmark stats could be contaminated by another active run.

## Milestone 5 - Tests And Verification

- [x] T025: Add episode memory tests.
- [x] T026: Add TODO state and tool tests.
- [x] T027: Add mission/report validation tests.
- [x] T028: Add static-audit policy tests.
- [x] T029: Add provider usage and proxy safety tests.
- [x] T030: Run focused unit tests for touched runtime, provider, benchmark, and event-session areas.
- [x] T031: Run full Python test suite.
- [x] T032: Run Ruff and mypy.
- [ ] T033: Run sanitized secure-code-hunt validation on app-01 and at least one additional app.
- [x] T034: Run documentation redaction checks for local endpoints, temp paths, API key names, hidden manifests, and answer-key content.
- [x] T035: Update `STATUS.md` with final verification results.
