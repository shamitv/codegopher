# CodeGopher v0.11 TODO - Discovery-Gated Chained Audits

This checklist is commit-oriented. Keep the feature general: app-01 is the regression case, not a source of app-specific hints.

## Milestone 0 - Planning Docs

- [x] T001: Create `docs/plans/v0.11/PLAN.md`.
- [x] T002: Create `docs/plans/v0.11/TODO.md`.
- [x] T003: Create `docs/plans/v0.11/STATUS.md`.

## Milestone 1 - Focus Queue Ranking

- [x] T004: Add file-family scoring for controllers, routes, auth/session, config, validators, uploads, jobs, webhooks, repositories, external calls, state-changing endpoints, and TS/TSX render sinks.
- [x] T005: Penalize repeated low-signal static asset matches such as CSS layout rules and generic static shell markup.
- [x] T006: Prefer representative paths across high-signal families before adding duplicate matches from the same file.
- [x] T007: Improve source graph ranking for route-to-auth, validator-to-controller, source-to-query, upload-to-mutation, webhook-to-fetch, secret-to-session, and data-to-render paths.

## Milestone 2 - Discovery Gates

- [x] T008: Add discovery-quality metrics separate from report quality and safety quality.
- [x] T009: Detect weak or zero coverage for high-risk source families.
- [x] T010: Trigger correction when a report claims no complete chains but high-risk discovery coverage is incomplete.
- [x] T011: Treat "not enough files inspected yet" as an acceptable incomplete outcome, but not as a completed no-findings result.

## Milestone 3 - Corrective Pass Behavior

- [x] T012: Render a compact missing-file-family worklist in corrective prompts.
- [x] T013: Ask correction to read missing high-risk files before repairing ledger format.
- [x] T014: Keep corrective work bounded by representative files so the prompt does not become a broad re-audit.
- [x] T015: Preserve existing report-quality corrections for ledger validity, exact evidence, safe-control classification, and contradictory conclusions.

## Milestone 4 - Mission And Skill Guidance

- [x] T016: Update the chained-audit mission contract to distinguish artifact completion from discovery completion.
- [x] T017: Update `chained-vulnerability-static-audit` guidance to require reviewed source-family coverage before final no-chain conclusions.
- [x] T018: Add pivot guidance so incomplete findings lead to adjacent source review, such as secret key to session/auth/role checks.
- [x] T019: Ensure static-only safety language remains unchanged.

## Milestone 5 - Benchmark Reporting

- [x] T020: Report safety quality, report quality, discovery quality, and hidden-chain recall as separate dimensions.
- [x] T021: Add per-family discovery summaries to benchmark analysis output.
- [x] T022: Add corrective-reason summaries that show whether correction was discovery-driven or format-driven.
- [x] T023: Keep raw benchmark artifacts outside committed docs unless summarized with placeholder-safe paths.

## Milestone 6 - Tests And Verification

- [x] T024: Add focus queue ranking unit tests for high-signal files outranking repeated static assets.
- [x] T025: Add discovery-gate tests for premature no-chain reports.
- [x] T026: Add corrective prompt tests for missing source-family worklists.
- [x] T027: Add evaluator tests for discovery-quality metrics.
- [x] T028: Run focused benchmark/harness tests.
- [x] T029: Run full Python tests.
- [x] T030: Run Ruff.
- [x] T031: Run mypy.
- [x] T032: Re-run sanitized secure-code-hunt app-01 and compare against the clean baseline.
- [x] T033: Update `STATUS.md` with implementation and verification results.
