# CodeGopher v0.9 TODO - Harder Chained Vulnerability Benchmark

This checklist is commit-oriented and scoped to development-only benchmark quality. Do not add a public `cgopher benchmark` command.

## Milestone 0 - Planning And Baseline

- [x] T001: Create v0.9 `PLAN.md` and `TODO.md`.
- [x] T002: Record v0.8 baseline caveat that both compared all-50 runs were Qwen-routed.
- [x] T003: Inventory current 50 manifests by language, framework, vulnerability family, chain count, and component count.
- [x] T004: Assign each app a target difficulty: medium, hard, or expert.
- [x] T005: Design upgraded chain metadata for all 50 apps before source-level benchmark reruns.

## Milestone 1 - Manifest Schema

- [x] T006: Extend manifest parsing for chain-level `difficulty`.
- [x] T007: Extend manifest parsing for `subtlety_tags`.
- [x] T008: Extend manifest parsing for `required_evidence`.
- [x] T009: Extend manifest parsing for `chain_prerequisites`.
- [x] T010: Extend manifest parsing for `negative_evidence`.
- [x] T011: Extend manifest parsing for `vulnerability_family`.
- [x] T012: Preserve backward compatibility with existing manifests during the transition.
- [x] T013: Add parser tests for multiple chains and new optional fields.

## Milestone 2 - Evaluator And Reporting

- [x] T014: Require stronger source evidence for component detection.
- [x] T015: Track missing required evidence per chain component.
- [x] T016: Track decoy or negative-evidence misfires.
- [x] T017: Add full-chain recall separate from component recall.
- [x] T018: Add recall summaries by difficulty tier.
- [x] T019: Add recall summaries by vulnerability family.
- [x] T020: Update per-app analysis Markdown with missing-evidence and decoy details.
- [x] T021: Update aggregate benchmark reports with difficulty and family metrics.
- [x] T022: Add evaluator and reporter unit tests for the new metrics.

## Milestone 3 - Corpus Upgrade

- [x] T023: Upgrade Python apps 01-05 with subtler chains and updated manifests.
- [x] T024: Upgrade Java apps 06-10 with subtler chains and updated manifests.
- [x] T025: Upgrade TypeScript apps 11-15 with subtler chains and updated manifests.
- [x] T026: Upgrade JavaScript apps 16-25 with subtler chains and updated manifests.
- [x] T027: Upgrade Java apps 26-30 with subtler chains and updated manifests.
- [x] T028: Upgrade JavaScript apps 31-40 with subtler chains and updated manifests.
- [x] T029: Upgrade Python apps 41-50 with subtler chains and updated manifests.
- [x] T030: Add realistic safe-code decoys near vulnerable flows in every app.
- [x] T031: Remove or rewrite source/docs/test hints containing benchmark or vulnerability labels.

## Milestone 4 - Validation

- [x] T032: Validate all 50 manifests parse.
- [x] T033: Validate all manifest file anchors exist in source.
- [x] T034: Validate required-evidence anchors exist in source.
- [x] T035: Validate sanitized temp copies contain no evaluator files.
- [x] T036: Validate sanitized temp copies contain no obvious benchmark hints.
- [x] T037: Run focused benchmark unit tests.
- [x] T038: Run full Python tests.
- [x] T039: Run Ruff.
- [x] T040: Run mypy.

## Milestone 5 - Real Benchmark

- [x] T041: Confirm proxy routing before using model labels.
- [x] T042: Run fixed-proxy Qwen all-50 benchmark.
- [x] T043: Archive v0.9 benchmark artifacts under `docs/plans/v0.9/report/<timestamp>`.
- [x] T044: Compare v0.9 results against the v0.8 historical Qwen baseline.
- [x] T045: Create or update v0.9 `STATUS.md` with implementation state and benchmark outcome.
- [x] T046: Mark completed TODO items with report links or commit references.
