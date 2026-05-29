# CodeGopher v0.13 Plan - Quality-Led Chained Audit Repair

## Summary

v0.13 is a quality and observability pass for chained vulnerability audits. It is
based on the v0.12 implemented-complexity reports and recovered raw run artifacts
for stamp `20260528-224739`, without copying raw logs, generated reports, temp
roots, endpoint values, API key names, proxy snapshots, or corpus paths into
committed documentation.

The v0.12 raw artifacts confirmed three important failure modes beyond the
committed aggregate summaries:

- Some Qwen attempts ended with malformed tool-call JSON, especially during
  retry or corrective work.
- Corrective passes can fail after an earlier usable report, so benchmark
  analysis must preserve per-attempt report snapshots and select the last
  completed usable attempt.
- Some sanitized workspaces still exposed answer-key filename references through
  visible source or test files, so preflight hygiene must be stricter.

Cost controls, wall-time ceilings, benchmark budget machinery, and per-app
timeout budget summaries are intentionally out of scope for v0.13. The current
goal is quality: valid ledgers, better evidence shape, safer hygiene signals,
better attempt diagnosis, and fewer shallow no-chain completions.

## Scope

- Keep benchmark tooling internal under `codegopher.devtools.benchmark`.
- Do not add a public benchmark command.
- Preserve static-only audit boundaries: no live probing, fuzzing, exploit
  execution, shell execution during chained audits, arbitrary writes, MCP calls,
  parent traversal, hidden metadata reads, or persistent memory writes.
- Commit only durable, sanitized aggregate conclusions and implementation plans.
- Keep generated benchmark event logs, stderr logs, temp workspaces, raw
  generated reports, raw proxy data, endpoints, API key names, usernames, and
  original corpus paths out of committed docs.

## Key Changes

### Corrective Episode Summaries

Add benchmark-level corrective episode summaries for repair prompts. Each summary
is bounded and redacted, and should be built from prior attempt logs, generated
report snapshots, parsed Candidate Chain Ledgers, tool calls, inspected files,
candidate evidence paths, safe-control classifications, missing evidence, and
open quality gates.

The summary must not paste raw report bodies or raw event streams into prompts.
It should provide compact state that helps the model continue from the current
audit instead of restarting discovery.

### Bounded Ledger Repair Pass

Add one final ledger-repair pass after the generic corrective pass when the
generated report exists but the parsed Candidate Chain Ledger is missing or
invalid.

The repair pass receives parsed validation errors and is constrained to repair:

- Missing or invalid `candidate_chains` JSON ledger structure.
- Missing `source`, `hop`, or `sink` evidence objects.
- Incomplete repo-relative `path`, exact `symbol`, and `line` or `line_range`
  evidence.
- Invalid or missing safe-control `classification`.
- Missing `missing_evidence` fields.

The pass must preserve existing complete, incomplete, and rejected candidate
conclusions unless source evidence supports a correction.

### Last-Good Attempt Preservation

Write per-attempt report snapshots and analyze the last completed usable attempt
when a later corrective or repair pass fails before `turn_complete`.

Attempt outcomes are classified as:

- `complete`
- `malformed_tool_arguments`
- `missing_turn_complete`
- `missing_report`
- `missing_writer_call`
- `quality_gate_failure`
- `policy_denied_metadata_search`
- `provider_error`

Benchmark summaries include `attempt_summaries`, `attempt_outcome_counts`, and
`last_good_attempt`.

### Safety And Hygiene Breakdown

Split safety and hygiene metrics so denied unsafe attempts do not look the same
as successful forbidden access.

Summaries include:

- Denied unsafe or metadata-search attempts.
- Successful forbidden metadata access.
- Answer-key leakage in visible source.
- Output leakage.
- Hygiene removal and residual-hint counts.

Sanitized validation workspaces must fail preflight if hidden manifests, removed
docs, `tests`, `src/test`, `__tests__`, or answer-key filename or terminology
references remain visible.

### Candidate-Flow Coverage

Add candidate-flow coverage separate from focus coverage and discovery quality.
Discovery counts as substantively complete only when reviewed high-risk source
families are represented in complete, incomplete, or rejected source-hop-sink
candidates.

This catches the v0.12 pattern where scans visited important source families but
still ended with shallow reports that did not connect reviewed source, hop, and
sink evidence into candidate flows.

### Quality-Only Composite Score

Add `composite_quality_score` to benchmark summaries:

| Dimension | Weight |
|---|---:|
| Complete-chain recall | 30% |
| Component recall | 20% |
| Ledger validity and exact evidence | 20% |
| Candidate-flow coverage | 15% |
| Safety and hygiene | 10% |
| Report writer and report completion | 5% |

The score intentionally excludes cost and wall time for v0.13.

## Interfaces

- Extend benchmark summaries with `attempt_summaries`,
  `attempt_outcome_counts`, `last_good_attempt`, `ledger_repair_used`,
  `candidate_flow_coverage`, `safety_hygiene_breakdown`, and
  `composite_quality_score`.
- Add the internal devtools flag `--no-ledger-repair-pass`.
- Keep `--no-corrective-second-pass` for isolating the generic corrective pass in
  tests.

## Test Plan

- Unit-test corrective episode summary rendering, redaction, bounds, and prompt
  injection resistance.
- Unit-test ledger repair triggers for missing JSON ledger, empty hop or sink
  evidence, invalid safe-control classification, missing `missing_evidence`, and
  incomplete path, symbol, or line evidence.
- Unit-test attempt classification for malformed streamed tool arguments,
  missing `turn_complete`, missing writer call, missing report, and mission
  quality-gate failure.
- Unit-test last-good-attempt selection so a failed repair pass does not erase a
  prior usable report.
- Unit-test hygiene preflight against hidden metadata names, answer-key terms,
  `tests`, `src/test`, and `__tests__`.
- Unit-test candidate-flow coverage separately from focus and discovery
  coverage.
- Snapshot-test aggregate reports and quality-score calculations.

## Real-Model Validation

Focused validation comes first:

- Models: `gpt-5.4-mini`, `Qwen/Qwen3.6-35B-A3B:deepinfra`, and the
  locally hosted Responses API model alias `Qwen 3.5 35B`.
- Apps: sanitized `app-05`, `app-10`, and `app-14`.

Full validation comes second only if focused validation improves ledger validity
without complete-chain recall regression:

- Models: the focused model set that passes the no-regression gate.
- Apps: all seven v0.12 implemented complexity apps.

Success criteria:

- Safety and hygiene preflight passes.
- The report writer is called for every completed app.
- Valid ledger rate improves over v0.12.
- Complete-chain recall does not regress.
- Malformed tool-call attempts are classified.
- Last-good reports are preserved.
- Committed summaries remain sanitized.
- Local-model summaries identify only the model alias and API family; raw
  endpoint URLs remain out of committed docs.

## Assumptions

- The recovered raw artifact root is validation input only and must not be copied
  into committed docs.
- v0.13 optimizes audit quality and observability, not cost or wall-time control.
- Static-only boundaries remain unchanged.
