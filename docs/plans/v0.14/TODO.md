# CodeGopher v0.14 TODO - Stream-Robust Chained Audit Quality

This checklist is implementation-oriented. Keep committed outputs sanitized and
avoid app-specific hints from validation corpora.

## Milestone 0 - Scope

- [x] T001: Create `docs/plans/v0.14/PLAN.md`.
- [x] T002: Keep benchmark tooling internal; do not add a public benchmark
  command.
- [x] T003: Keep the chained audit static-only.
- [x] T004: Keep raw logs, generated reports, temp roots, proxy snapshots,
  endpoints, API key names or values, usernames, and corpus paths out of
  committed docs.

## Milestone 1 - Malformed Tool-Call Robustness

- [x] T005: Add structured parse metadata for malformed streamed tool-call JSON.
- [x] T006: Emit provider-recovery events for malformed tool-call recovery.
- [x] T007: Narrow recovery prompts to the failed tool schema when known.
- [x] T008: Add current-state report-writing fallback for repeated malformed
  tool-call failures during chained audits.
- [x] T009: Summarize provider recovery attempts, tool-call parse errors, and
  recovered malformed calls in benchmark outputs.

## Milestone 2 - Candidate Flow Repair

- [x] T010: Add bounded candidate-flow repair after ledger repair.
- [x] T011: Add internal flag `--no-candidate-flow-repair-pass`.
- [x] T012: Preserve the existing candidate statuses: `complete`,
  `incomplete`, and `rejected`.
- [x] T013: Record candidate-flow repair usage and reasons in summaries.

## Milestone 3 - Hygiene And Scoring

- [x] T014: Split exact answer-key leakage from generic security vocabulary.
- [x] T015: Add output-leakage markers for temp roots, local paths, endpoint
  values, proxy/admin URLs, API key names or values, and corpus paths.
- [x] T016: Keep generic security vocabulary as diagnostic signal, not a safety
  failure.

## Milestone 4 - Tests

- [x] T017: Unit-test structured JSON parse metadata.
- [x] T018: Unit-test provider malformed-tool metadata.
- [x] T019: Unit-test provider-recovery event emission.
- [x] T020: Unit-test candidate-flow repair triggering.
- [x] T021: Unit-test safety/hygiene metric de-noising and output leakage.
- [x] T022: Run the focused unit-check command from the validation plan.

## Milestone 5 - Focused Real-Model Validation

- [x] T023: Run `gpt-5.4-mini` on sanitized `app-05`, `app-10`, and `app-14`
  with a fresh proxy run.
- [x] T024: Run local Responses API alias `Qwen 3.5 35B` on sanitized `app-05`,
  `app-10`, and `app-14` with a fresh proxy run and longer timeout.
- [x] T025: Compare components, complete chains, ledger validity, writer/report
  completion, provider errors, malformed outcomes, recovered malformed calls,
  candidate-flow repairs, and last-good behavior.
- [x] T026: Update sanitized focused-validation docs.
- [x] T027: Run redaction checks before commit.
- [x] T028: Commit and push `improve_vuln_detection`.

Focused validation note: `gpt-5.4-mini` produced `12/19` component recall,
`4/8` complete-chain recall, `3/3` valid ledgers, and report writer completion
for all focused apps. Complete-chain recall and ledger validity held, but
component recall regressed by one item from v0.13. Local `Qwen 3.5 35B` was
invalid as a quality comparison because the local upstream returned provider
errors for every benchmark attempt; a lightweight post-run hello check also
failed through the same path. Full seven-app validation remains blocked.
