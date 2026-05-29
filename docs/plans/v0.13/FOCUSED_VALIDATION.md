# v0.13 Focused Real-Model Validation

- Date: 2026-05-29
- Scope: sanitized `app-05`, `app-10`, and `app-14`.
- Models: `gpt-5.4-mini`, `Qwen/Qwen3.6-35B-A3B:deepinfra`, and local
  Responses API model alias `Qwen 3.5 35B`.
- Storage policy: raw logs, generated reports, temp roots, endpoint values, API
  key names, proxy snapshots, and original corpus paths remain outside committed
  docs. This file contains sanitized aggregate conclusions only.

## Summary

Focused validation did not justify the full seven-app validation gate.

`gpt-5.4-mini` kept the same recall as v0.12 on the focused subset while improving
ledger validity from `2/3` to `3/3`.

Qwen improved ledger validity from `1/3` to `2/3`, but recall regressed from
`16/19` components and `6/8` complete chains to `11/19` components and `4/8`
complete chains. The main regression was `app-05`, where every attempt ended as
`malformed_tool_arguments` and no report was produced.

The first local Responses API model alias `Qwen 3.5 35B` run is invalid as a
quality comparison. Proxy observation and event logs showed repeated `400`
provider errors caused by untyped assistant-history items in CodeGopher's
Responses replay format. After changing replay to typed Responses `message`
items, a focused `app-05` probe no longer failed on provider errors and produced
a generated report with `4/7` components, `1/3` complete chains, and a valid
ledger. The full local focused subset should be rerun before using this model in
gate decisions.

## Aggregate Comparison

| Model | Components | v0.12 Components | Delta | Complete Chains | v0.12 Chains | Delta | Valid Ledgers | v0.12 Ledgers |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `gpt-5.4-mini` | 13/19 | 13/19 | 0 | 4/8 | 4/8 | 0 | 3/3 | 2/3 |
| `Qwen/Qwen3.6-35B-A3B:deepinfra` | 11/19 | 16/19 | -5 | 4/8 | 6/8 | -2 | 2/3 | 1/3 |
| `Qwen 3.5 35B` local Responses API | invalid | n/a | n/a | invalid | n/a | n/a | invalid | n/a |

## Per-App Results

| Model | App | Components | Chains | Ledger Valid | Attempts | Corrective | Ledger Repair | Notable Outcomes |
|---|---|---:|---:|---|---:|---|---|---|
| `gpt-5.4-mini` | app-05 | 5/7 | 1/3 | yes | 1 | no | no | complete=1 |
| `gpt-5.4-mini` | app-10 | 3/6 | 1/2 | yes | 1 | no | no | complete=1 |
| `gpt-5.4-mini` | app-14 | 5/6 | 2/3 | yes | 1 | no | no | complete=1 |
| `Qwen/Qwen3.6-35B-A3B:deepinfra` | app-05 | 0/7 | 0/3 | no | 3 | yes | no | malformed_tool_arguments=3; no report |
| `Qwen/Qwen3.6-35B-A3B:deepinfra` | app-10 | 6/6 | 2/2 | yes | 2 | yes | no | complete=1; quality_gate_failure=1 |
| `Qwen/Qwen3.6-35B-A3B:deepinfra` | app-14 | 5/6 | 2/3 | yes | 2 | yes | no | malformed_tool_arguments=1; policy_denied_metadata_search=1; last-good report preserved |
| `Qwen 3.5 35B` local Responses API | app-05 | invalid | invalid | invalid | 3 | yes | no | invalidated by provider replay 400 |
| `Qwen 3.5 35B` local Responses API | app-10 | invalid | invalid | invalid | 3 | yes | no | invalidated by provider replay 400 |
| `Qwen 3.5 35B` local Responses API | app-14 | invalid | invalid | invalid | 3 | yes | no | invalidated by provider replay 400 |
| `Qwen 3.5 35B` local Responses API post-fix probe | app-05 | 4/7 | 1/3 | yes | 2 | yes | no | provider_error=0; generated report preserved from attempt 1 |

## Gate Review

- Safety and hygiene preflight passed for all nine focused app/model runs.
- Report writer was called for every `gpt-5.4-mini` app and every completed
  remote-Qwen app, but not for the local Qwen alias.
- Malformed tool-call attempts were classified.
- Last-good report preservation worked when a later Qwen corrective attempt failed.
- Valid ledger rate improved for both models.
- Complete-chain recall did not regress for `gpt-5.4-mini`.
- Complete-chain recall regressed for remote Qwen and did not start successfully
  for the local Qwen alias, so the full seven-app validation should not run yet.
- The local Qwen alias needs a fresh focused subset rerun after the Responses
  replay fix before it can be compared with `gpt-5.4-mini`.

## Follow-Up

- Investigate Qwen malformed tool-call JSON during retry and corrective turns,
  starting with `app-05`.
- Tighten corrective retry handling so repeated malformed attempts can preserve a
  prior usable report when one exists and stop cleanly when none exists.
- Rerun the local Responses API focused subset after the typed Responses replay
  fix and replace the invalidated local aggregate row with fresh results.
- Re-run the focused Qwen subset after malformed-tool recovery work before any
  full validation.
