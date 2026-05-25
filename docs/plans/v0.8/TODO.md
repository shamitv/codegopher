# CodeGopher v0.8 Development TODO

This checklist is commit-oriented and scoped to internal benchmark infrastructure. Do not add a public `cgopher benchmark` command.

## Milestone 0 - Planning And Docs

- [x] T001: Create v0.8 plan, status, and TODO docs.
- [x] T002: Revise v0.8 scope from public benchmark mode to development-only benchmark infrastructure.
- [x] T003: Update product roadmap to reflect internal v0.8 scope and defer richer IDE UI.

## Milestone 1 - Internal Benchmark Package

- [x] T004: Add `codegopher.devtools.benchmark` namespace.
- [x] T005: Add `.vulns` manifest and suite parsing.
- [x] T006: Add code-only workspace isolation that removes `README.md`, `impl_plan.md`, `.vulns`, and nested copies.
- [x] T007: Add subprocess execution for `cgopher --events` with explicit model, endpoint, API family, API key env, replay flag, timeout, and retry settings.
- [x] T008: Archive JSONL events, stderr, generated report, final text, ground truth, per-app analysis, and aggregate report.

## Milestone 2 - Evaluation

- [x] T009: Add event parsing and event count summaries.
- [x] T010: Add static safety analysis for unsafe tools, parent/original paths, removed docs, and denied tool results.
- [x] T011: Add ground-truth component recall scoring.
- [x] T012: Add report quality signals: source-reference hits, line-reference count, and unmatched candidate chain titles.
- [x] T013: Avoid precision/F1 claims unless manifests are exhaustive.

## Milestone 3 - Audit Skill Quality

- [x] T014: Require file path, line number/range, and symbol evidence for every chain source, hop, and sink.
- [x] T015: Require the report writer to be called even when no chains are found.
- [x] T016: Codify High/Medium/Low confidence calibration.
- [x] T017: Require a cross-cutting weaknesses section.

## Milestone 4 - Tests

- [x] T018: Add unit tests for manifest and suite parsing.
- [x] T019: Add unit tests for workspace isolation and harness artifact creation.
- [x] T020: Add unit tests for safety, recall, and report-quality evaluation.
- [x] T021: Add unit tests for aggregate report rendering.
- [x] T022: Add mocked integration test for the internal runner.
- [x] T023: Add regression test that public `cgopher benchmark` is not available.

## Milestone 5 - Verification And Rescan

- [x] T024: Run targeted v0.8 tests.
- [x] T025: Run full Python tests.
- [x] T026: Run Ruff and mypy.
- [x] T027: Run VS Code compile/lint/tests if touched.
- [x] T028: Run internal real-LLM benchmark on the three secure-code-hunt apps.
- [x] T029: Update this TODO and STATUS with final results.
