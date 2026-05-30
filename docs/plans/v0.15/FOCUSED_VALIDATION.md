# v0.15 Focused Real-Model Validation

- Date: 2026-05-30
- Scope: sanitized `app-05`, `app-10`, and `app-14`.
- Models: `gpt-5.4-mini` and local Responses API alias `Qwen 3.5 35B`.
- Storage policy: raw logs, generated reports, temp roots, endpoint values, API
  key names, proxy snapshots, and original corpus paths remain outside committed
  docs. This file contains sanitized aggregate conclusions only.

## Summary

Focused validation did not unblock full seven-app validation.

`gpt-5.4-mini` produced clean ledgers and writer completion, but recall regressed
from the v0.14 focused baseline. It found `11/19` components and `3/8` complete
chains, down from `12/19` components and `4/8` complete chains in v0.14.

Local `Qwen 3.5 35B` passed the lightweight Responses/proxy hello preflight and
completed all three focused apps. That is a material transport improvement over
v0.14, where the local path did not reach workspace inspection. The quality run
found `17/19` components and `6/8` complete chains, but it did not clear all
quality gates because one ledger was invalid, malformed tool-call attempts
remained frequent, and one app had an answer-key leakage signal in visible
source diagnostics.

## Aggregate Comparison

| Model | Components | v0.14 Components | Delta | Complete Chains | v0.14 Chains | Delta | Valid Ledgers | Writer Called | Provider/Parse Recovery |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `gpt-5.4-mini` | 11/19 | 12/19 | -1 | 3/8 | 4/8 | -1 | 3/3 | 3/3 | none |
| `Qwen 3.5 35B` local Responses API | 17/19 | n/a | n/a | 6/8 | n/a | n/a | 2/3 | 3/3 | malformed tool-call recovery present |

## Per-App Results

| Model | App | Components | Chains | Ledger Valid | Attempts | Corrective | Ledger Repair | Candidate-Flow Repair | Notable Outcomes |
|---|---|---:|---:|---|---:|---|---|---|---|
| `gpt-5.4-mini` | app-05 | 4/7 | 1/3 | yes | 1 | no | no | no | complete=1 |
| `gpt-5.4-mini` | app-10 | 2/6 | 0/2 | yes | 1 | no | no | no | complete=1 |
| `gpt-5.4-mini` | app-14 | 5/6 | 2/3 | yes | 1 | no | no | no | complete=1; candidate-flow gaps remained |
| `Qwen 3.5 35B` local Responses API | app-05 | 6/7 | 2/3 | yes | 4 | yes | no | yes | malformed_tool_arguments=3; quality_gate_failure=1; repair failed missing writer; last-good report preserved |
| `Qwen 3.5 35B` local Responses API | app-10 | 6/6 | 2/2 | yes | 1 | no | no | no | complete=1 |
| `Qwen 3.5 35B` local Responses API | app-14 | 5/6 | 2/3 | no | 4 | yes | yes | no | malformed_tool_arguments=3; missing_turn_complete=1; last-good report preserved |

## Proxy And Event Review

- A separate proxy run was created for each model.
- The GPT proxy run completed with 21 requests and no proxy error count.
- The local Qwen proxy run completed with 183 requests and no proxy error count.
- GPT had no malformed tool-call JSON and no provider-recovery events.
- Qwen had repeated malformed tool-call recovery on `app-05` and `app-14`.
- Qwen was transport-healthy for the focused benchmark, but local throughput was
  much slower than the cloud path.

## Gate Review

- Focused unit tests passed.
- GPT failed the v0.15 recall gates: components were `11/19` instead of at least
  `13/19`, and complete chains were `3/8` instead of at least `4/8`.
- GPT passed ledger validity and writer completion with `3/3` valid ledgers and
  `3/3` writer calls.
- Qwen passed the transport-health gate and completed all focused apps.
- Qwen exceeded the GPT recall target, but failed full quality gating because
  ledgers were `2/3`, malformed tool-call attempts persisted, and one app had an
  answer-key leakage diagnostic.
- Candidate-flow repair was exercised on Qwen `app-05`, but the repair attempt
  did not call the report writer; last-good selection preserved the prior usable
  report.
- Full seven-app validation remains blocked.

## Follow-Up

- Tune GPT source-navigation so the new focus queue does not reduce recall.
- Keep Qwen in validation scope, but treat local throughput and malformed
  tool-call recovery as first-class blockers.
- Investigate why Qwen `app-14` ledger repair still left an invalid ledger.
- Tighten candidate-flow repair so missing writer calls are avoided, not only
  classified.
