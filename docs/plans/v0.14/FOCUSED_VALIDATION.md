# v0.14 Focused Real-Model Validation

- Date: 2026-05-30
- Scope: sanitized `app-05`, `app-10`, and `app-14`.
- Models: `gpt-5.4-mini` and local Responses API alias `Qwen 3.5 35B`.
- Storage policy: raw logs, generated reports, temp roots, endpoint values, API
  key names, proxy snapshots, and original corpus paths remain outside committed
  docs. This file contains sanitized aggregate conclusions only.

## Summary

Focused validation did not unblock full seven-app validation.

`gpt-5.4-mini` stayed stable on complete-chain recall and ledger validity, but
component recall dropped by one item versus v0.13 focused validation. It produced
`12/19` components, `4/8` complete chains, `3/3` valid ledgers, and report writer
completion for all three apps.

Local `Qwen 3.5 35B` is not a valid quality comparison for this run. The fresh
post-fix run produced only provider errors after the local upstream became
unavailable, and a lightweight post-run hello check through the same proxy path
also returned an upstream connection failure. Treat the Qwen result as a
transport failure, not as model-quality recall.

## Aggregate Comparison

| Model | Components | v0.13 Components | Delta | Complete Chains | v0.13 Chains | Delta | Valid Ledgers | Writer Called | Provider/Parse Recovery |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `gpt-5.4-mini` | 12/19 | 13/19 | -1 | 4/8 | 4/8 | 0 | 3/3 | 3/3 | none |
| `Qwen 3.5 35B` local Responses API | n/a | 12/19 | n/a | n/a | 5/8 | n/a | n/a | 0/3 | transport failure |

## Per-App Results

| Model | App | Components | Chains | Ledger Valid | Attempts | Corrective | Ledger Repair | Candidate-Flow Repair | Notable Outcomes |
|---|---|---:|---:|---|---:|---|---|---|---|
| `gpt-5.4-mini` | app-05 | 4/7 | 1/3 | yes | 2 | yes | no | no | complete=2 |
| `gpt-5.4-mini` | app-10 | 3/6 | 1/2 | yes | 1 | no | no | no | complete=1 |
| `gpt-5.4-mini` | app-14 | 5/6 | 2/3 | yes | 3 | yes | no | yes | complete=1; quality_gate_failure=1; missing_writer_call=1; last-good report preserved |
| `Qwen 3.5 35B` local Responses API | app-05 | n/a | n/a | no | 3 | yes | no | no | provider_error=3; no report |
| `Qwen 3.5 35B` local Responses API | app-10 | n/a | n/a | no | 3 | yes | no | no | provider_error=3; no report |
| `Qwen 3.5 35B` local Responses API | app-14 | n/a | n/a | no | 3 | yes | no | no | provider_error=3; no report |

## Proxy And Event Review

- A separate proxy run was created for each model.
- The GPT proxy run completed with 36 requests.
- The local Qwen proxy run completed with 27 requests, but every benchmark
  attempt surfaced provider errors from upstream connection failures.
- GPT had no malformed tool-call JSON and no provider-recovery events.
- Local Qwen had no malformed-tool recovery signal in the fresh post-fix run
  because requests failed before usable model output was streamed.

## Gate Review

- Focused unit tests passed.
- GPT report writer completion passed for all focused apps.
- GPT valid ledger rate remained `3/3`.
- GPT complete-chain recall did not regress, but component recall regressed from
  `13/19` to `12/19`.
- Candidate-flow repair was exercised on GPT `app-14`, but the repair attempt did
  not produce a new usable writer call; last-good attempt selection preserved the
  prior usable report.
- Local Qwen focused validation is blocked by local upstream availability.
- Full seven-app validation remains blocked.

## Follow-Up

- Re-run local Qwen only after the local upstream passes a lightweight hello
  check.
- Investigate why candidate-flow repair can still fail to produce a writer call.
- Tune GPT candidate-flow repair so it improves coverage without component
  recall regression.
