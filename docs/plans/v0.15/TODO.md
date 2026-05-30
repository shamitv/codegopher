# CodeGopher v0.15 TODO - Recall Recovery And Candidate-Flow Repair

This checklist is implementation-oriented. Keep it focused on the successful
GPT source-navigation path and the remaining quality gaps. Ignore the local
Qwen transport failure for this slice.

## Milestone 0 - Scope And Baseline

- [x] T001: Create `docs/plans/v0.15/PLAN.md`.
- [x] T002: Create `docs/plans/v0.15/TODO.md`.
- [x] T003: Base the slice on the v0.14 GPT-success path and remaining source
  coverage gaps.
- [x] T004: Exclude the local Qwen provider failure from v0.15 success/failure
  analysis.

## Milestone 1 - Coverage Recovery

- [ ] T005: Increase `auth_session` coverage in the focused chained-audit path.
- [ ] T006: Revisit the missing last hop in partially detected chains.
- [ ] T007: Improve entry-point-to-supporting-code expansion for the uncovered
  high-risk families.
- [ ] T008: Preserve the broad source-family sweep pattern that worked in
  v0.14.

## Milestone 2 - Candidate-Flow Repair

- [ ] T009: Make candidate-flow repair produce measurable coverage gains when
  the ledger is already valid.
- [ ] T010: Keep candidate-flow repair from regressing report quality or valid
  ledgers.
- [ ] T011: Ensure repair attempts can add new evidence instead of only
  preserving the last good report.
- [ ] T012: Keep TODO updates aligned with candidate-flow repair progress.

## Milestone 3 - Report Quality And Stability

- [ ] T013: Preserve report-writer completion for all focused apps.
- [ ] T014: Maintain valid ledgers while improving component recall.
- [ ] T015: Keep report conclusions source-grounded and sanitized.
- [ ] T016: Separate corrective report repair from discovery repair so the
  failure reason is clear.

## Milestone 4 - Validation

- [ ] T017: Re-run focused validation on the sanitized `app-05`, `app-10`, and
  `app-14` subset after the coverage-repair changes.
- [ ] T018: Compare component recall, full-chain recall, and valid-ledger rate
  against the v0.14 GPT baseline.
- [ ] T019: Confirm the Qwen transport failure is not used as a quality signal
  for this slice.
- [ ] T020: Update v0.15 status/docs only after the source-navigation results
  are verified.
