# CodeGopher v0.15 TODO - Recall Recovery With Journey Reporting

This checklist is implementation-oriented. Keep it focused on the successful
GPT source-navigation path, the remaining quality gaps, and Qwen validation
health. Treat Qwen transport failures separately from model-quality results.

## Milestone 0 - Scope And Baseline

- [x] T001: Create `docs/plans/v0.15/PLAN.md`.
- [x] T002: Create `docs/plans/v0.15/TODO.md`.
- [x] T003: Base the slice on the v0.14 focused baseline: GPT `12/19`
  components, `4/8` complete chains, `3/3` valid ledgers, and `3/3` writer
  completion.
- [x] T004: Keep local `Qwen 3.5 35B` in scope while classifying transport
  failures separately from quality metrics.

## Milestone 1 - Coverage Recovery Implementation

- [x] T005: Add evidence-first focus queue guidance for `auth_session`,
  privileged state-changing paths, `repositories_query`, and
  `webhooks_outbound`.
- [x] T006: Add final-hop bridging guidance before marking chains incomplete.
- [x] T007: Improve entry-point-to-supporting-code expansion for uncovered
  high-risk families across routes/controllers, guards, services,
  repositories, config, jobs, and consumers.
- [x] T008: Preserve the broad source-family sweep pattern that worked in
  v0.14.

## Milestone 2 - Candidate-Flow Repair

- [x] T009: Require candidate-flow repair to continue from current mission state
  instead of restarting discovery.
- [x] T010: Require candidate-flow repair to call
  `write_chained_vulnerability_report` when the writer is available.
- [x] T011: Classify repair attempts that miss the writer call as repair
  failures while preserving the last-good report.
- [x] T012: Ensure repair attempts add or explicitly reject evidence for missing
  source families using only `complete`, `incomplete`, or `rejected`.
- [x] T013: Keep TODO updates aligned with candidate-flow repair progress so
  partial evidence is not lost.

## Milestone 3 - Report Quality And Stability

- [x] T014: Preserve report-writer completion for all focused apps.
- [x] T015: Maintain valid ledgers while improving component recall.
- [x] T016: Keep report conclusions source-grounded and sanitized.
- [x] T017: Separate corrective report repair from discovery repair so the
  failure reason is clear.
- [x] T018: Keep chained audits static-only: no live probing, fuzzing, exploit
  execution, shell execution during audits, MCP calls, arbitrary writes, or
  memory writes.
- [x] T019: Treat arbitrary `write_file` cleanup as a failed repair path when
  the report writer was available.

## Milestone 4 - Focused Validation

- [x] T020: Run focused unit checks for the changed skill, benchmark, evaluator,
  and policy paths.
- [x] T021: Run focused validation with `gpt-5.4-mini` on sanitized `app-05`,
  `app-10`, and `app-14`.
- [x] T022: Run local Qwen transport-health preflight through the local
  Responses/proxy path.
- [x] T023: If Qwen preflight passes, run focused validation with local
  `Qwen 3.5 35B` on sanitized `app-05`, `app-10`, and `app-14`.
- [x] T024: If Qwen preflight or benchmark startup fails, document Qwen as
  transport-blocked and do not count recall as model quality. Outcome: preflight
  passed and quality validation ran.
- [x] T025: Compare GPT results against v0.14: require at least `13/19`
  components, at least `4/8` complete chains, `3/3` valid ledgers, and `3/3`
  writer completion.
- [x] T026: Compare Qwen components, complete chains, valid ledgers, writer
  completion, malformed-tool outcomes, provider errors, and last-good behavior
  when transport health permits a benchmark run.
- [x] T027: Confirm no new output leakage, unsafe tool-use regression, or
  answer-key leakage in focused outputs.

## Milestone 5 - Documentation And Redaction

- [x] T028: Create `docs/plans/v0.15/FOCUSED_VALIDATION.md` with sanitized
  aggregate and per-app focused results.
- [x] T029: Create `docs/plans/v0.15/FOCUSED_VALIDATION_JOURNEY.md` with
  sanitized per-model and per-app source-navigation analysis.
- [x] T030: In the journey report, summarize attempts, tool usage, repair
  behavior, findings, misses, last-good preservation, and safety/hygiene
  observations.
- [x] T031: Include Qwen's actual journey if transport succeeds; if blocked,
  state clearly that Qwen did not reach workspace inspection.
- [x] T032: Run redaction checks for raw logs, generated reports, temp roots,
  endpoints, proxy/admin URLs, API key names or values, usernames, and original
  corpus paths before committing docs.

Focused validation note: `gpt-5.4-mini` regressed to `11/19` component recall
and `3/8` complete-chain recall while preserving `3/3` valid ledgers and `3/3`
writer completion. Local `Qwen 3.5 35B` passed transport preflight and completed
the focused subset with `17/19` component recall, `6/8` complete-chain recall,
`2/3` valid ledgers, and `3/3` writer completion. Full validation remains
blocked because GPT recall regressed and Qwen still has malformed tool-call,
ledger-validity, and hygiene diagnostics.
