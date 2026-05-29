# CodeGopher v0.13 TODO - Quality-Led Chained Audit Repair

This checklist is implementation-oriented. Keep changes general and avoid
app-specific hints from validation corpora.

## Milestone 0 - Planning And Scope

- [x] T001: Create `docs/plans/v0.13/PLAN.md`.
- [x] T002: Create `docs/plans/v0.13/TODO.md`.
- [x] T003: Keep cost controls, wall-time ceilings, benchmark budget machinery,
  and per-app timeout budget summaries out of v0.13 scope.
- [x] T004: Document that raw logs, generated reports, temp roots, proxy
  snapshots, endpoints, API key names, and corpus paths must not be committed.

## Milestone 1 - Attempt Preservation And Classification

- [x] T005: Preserve per-attempt generated-report snapshots.
- [x] T006: Select the last completed usable attempt when later corrective or
  repair attempts fail before `turn_complete`.
- [x] T007: Add attempt summaries with outcome, event counts, tool counts,
  writer-call status, and report-snapshot status.
- [x] T008: Add attempt outcome counts for `complete`,
  `malformed_tool_arguments`, `missing_turn_complete`, `missing_report`,
  `missing_writer_call`, `quality_gate_failure`,
  `policy_denied_metadata_search`, and `provider_error`.

## Milestone 2 - Corrective And Ledger Repair

- [x] T009: Add bounded corrective episode summaries from prior attempts,
  report snapshots, parsed ledgers, inspected files, candidate evidence, safe
  controls, missing evidence, and open quality gates.
- [x] T010: Redact and bound corrective episode summaries.
- [x] T011: Add a bounded ledger-repair pass driven by parsed validation
  errors.
- [x] T012: Add internal devtools flag `--no-ledger-repair-pass`.
- [ ] T013: Tune ledger-repair prompt wording after focused real-model
  validation.

## Milestone 3 - Hygiene And Safety Metrics

- [x] T014: Remove `tests`, `src/test`, and `__tests__` from sanitized
  validation workspaces.
- [x] T015: Sanitize hidden metadata filename references from visible source.
- [x] T016: Block static-audit metadata filename searches, including escaped
  filename queries.
- [x] T017: Split safety and hygiene summaries into denied unsafe attempts,
  successful forbidden access, visible-source leakage, and output leakage.
- [x] T018: Review focused validation hygiene artifacts for residual source
  hints before any aggregate report is committed.

## Milestone 4 - Candidate Flow And Scoring

- [x] T019: Add candidate-flow coverage for complete, incomplete, and rejected
  source-hop-sink candidates.
- [x] T020: Add candidate-flow gaps to corrective reasons when discovery is
  otherwise complete.
- [x] T021: Add `composite_quality_score` with v0.13 quality-only weights.
- [x] T022: Render candidate-flow and composite-score data in benchmark
  reports.

## Milestone 5 - Tests

- [x] T023: Unit-test corrective episode summary rendering, redaction, bounds,
  and prompt injection resistance.
- [x] T024: Unit-test ledger repair triggers for missing JSON ledger, empty
  hop/sink evidence, invalid safe-control classification, missing
  `missing_evidence`, and incomplete path/symbol/line evidence.
- [x] T025: Unit-test attempt classification for malformed streamed tool
  arguments, missing `turn_complete`, missing writer call, missing report, and
  mission quality-gate failure.
- [x] T026: Unit-test last-good-attempt selection so a failed repair pass does
  not erase a prior usable report.
- [x] T027: Unit-test hygiene preflight against hidden metadata names,
  answer-key terms, `tests`, `src/test`, and `__tests__`.
- [x] T028: Unit-test candidate-flow coverage separately from focus and
  discovery coverage.
- [x] T029: Snapshot-test aggregate reports and quality-score calculations.
- [x] T030: Run focused unit tests for touched benchmark, evaluator, reporter,
  hygiene, and static-audit policy modules.

## Milestone 6 - Real-Model Validation

- [x] T031: Run focused validation with `gpt-5.4-mini` on sanitized `app-05`,
  `app-10`, and `app-14`.
- [x] T032: Run focused validation with
  `Qwen/Qwen3.6-35B-A3B:deepinfra` on sanitized `app-05`, `app-10`, and
  `app-14`.
- [x] T033: Run focused validation with local Responses API model alias
  `Qwen 3.5 35B` on sanitized `app-05`, `app-10`, and `app-14`.
- [x] T034: Confirm focused validation safety and hygiene preflight passes.
- [ ] T035: Confirm valid ledger rate improves over v0.12 without
  complete-chain recall regression.
- [x] T036: Confirm report writer is called for every completed focused app.
- [x] T037: Confirm malformed tool-call attempts are classified.
- [x] T038: Confirm last-good reports are preserved after failed corrective or
  repair attempts.
- [ ] T039: If focused validation passes, run the selected model set on all
  seven v0.12 implemented complexity apps.
- [ ] T040: Commit only sanitized aggregate conclusions from validation.

Focused validation note: `gpt-5.4-mini` held recall flat and improved ledger
validity. Remote Qwen regressed from `16/19` to `11/19` component recall and
from `6/8` to `4/8` complete-chain recall on the focused subset. The local
Responses API model alias `Qwen 3.5 35B` completed the harness run but produced
no reports, with `0/19` component recall, `0/8` complete-chain recall, and
`0/3` valid ledgers. Full validation is blocked until the Qwen report-completion
and malformed-tool-call regressions are repaired.
