# CodeGopher v0.16 TODO

## Implementation

- [x] Reorder system prompt sections so loaded skills appear before volatile memory, episode, TODO, and mission content.
- [x] Add environment and CLI output-token override support.
- [x] Add internal benchmark output-token pass-through.
- [x] Add concise local-model report-writing guidance to the benchmark prompt.
- [x] Add local Qwen focused validation automation script.

## Tests

- [x] Run focused unit tests:
  - `tests/unit/test_config_loader.py`
  - `tests/unit/test_config_schema.py`
  - `tests/unit/test_context_builder.py`
  - `tests/unit/test_agent_session.py`
  - `tests/unit/test_benchmark_harness.py`
  - `tests/unit/test_benchmark_proxy.py`
- [x] Run lint on touched Python files.

## Local Qwen Validation

- [x] Run the local Responses/proxy focused validation script.
- [x] Compare against the v0.15 focused local Qwen baseline:
  - Components: `17/19`
  - Complete chains: `6/8`
  - Valid ledgers: `2/3`
  - Writer completion: `3/3`
- [x] Record malformed tool-call attempts, output-limit hits, writer completion, valid ledgers, recall, last-good behavior, and cache observations.
- [x] If transport fails, classify it separately from model quality. Transport passed; quality/safety findings are recorded separately.

## Documentation

- [x] Create `docs/plans/v0.16/PLAN.md`.
- [x] Create `docs/plans/v0.16/TODO.md`.
- [x] Create or update `docs/plans/v0.16/LOCAL_QWEN_VALIDATION.md` after the focused rerun.
- [x] Run redaction checks before any commit.

## Gate For Next Slice

- [x] Focused local Qwen validation has no recall regression and writer completion remains `3/3`, or the remaining blocker is documented with sanitized evidence.
