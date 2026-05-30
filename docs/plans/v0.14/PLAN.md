# CodeGopher v0.14 Plan: Stream-Robust Chained Audit Quality

## Summary

v0.14 hardens the chained-audit validation loop after v0.13 showed a split
between provider transport success and client-side tool-call parse failures. The
goal is to preserve quality progress from valid reports while making malformed
tool-call recovery, candidate-flow repair, and hygiene scoring more observable.

This plan remains quality-led. It does not add public benchmark commands, cost
controls, wall-time budgets, dynamic probing, exploit execution, shell execution
during audits, MCP calls, arbitrary writes, or persistent memory writes.

## Key Changes

- Add structured malformed tool-call parse metadata without storing raw tool
  arguments in committed summaries.
- Emit provider-recovery events so benchmark summaries can distinguish recovered
  malformed calls from final malformed failures.
- Narrow malformed-tool recovery prompts to the failed tool schema when known.
- For chained audits, fall back to a current-state report-writing prompt after
  repeated malformed tool-call failures.
- Add a bounded candidate-flow repair pass after ledger repair when discovery is
  complete and the JSON ledger is valid but reviewed high-risk source families
  lack complete, incomplete, or rejected candidates.
- Split exact answer-key leakage from generic security vocabulary diagnostics.
- Treat temp roots, home paths, endpoint/admin URLs, API key names or values,
  and original corpus paths as output-leakage markers for benchmark evaluation.

## Interfaces

- Benchmark work remains internal under `codegopher.devtools.benchmark`.
- Add internal flag `--no-candidate-flow-repair-pass`.
- Extend benchmark summaries with `provider_recovery_attempts`,
  `tool_call_parse_errors`, `recovered_malformed_tool_arguments`,
  `candidate_flow_repair_used`, and `candidate_flow_repair_reasons`.
- Extend safety/hygiene summaries with generic security vocabulary diagnostics
  that do not count as exact answer-key leakage.

## Validation

Focused validation comes first:

- Models: `gpt-5.4-mini` and local Responses API alias `Qwen 3.5 35B`.
- Apps: sanitized `app-05`, `app-10`, and `app-14`.
- Local Qwen uses a longer internal timeout because the validation host uses a
  laptop GPU.
- Each model gets a separate proxy run.

Full seven-app validation stays blocked until focused validation shows no
regression for GPT and local Qwen clears the prior no-report `app-05` blocker.

## Storage Policy

Do not commit raw logs, generated reports, temp roots, proxy snapshots, endpoint
values, API key names, API key values, local usernames, or original corpus paths.
Only sanitized aggregate conclusions belong in committed docs.
