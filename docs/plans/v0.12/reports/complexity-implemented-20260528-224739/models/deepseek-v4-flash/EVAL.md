# deepseek-v4-flash Evaluation

- Stamp: `20260528-224739`
- Apps scanned: 7
- Run status: complete

## Summary

| Metric | Value |
|---|---:|
| Component recall | 33/41 (80.5%) |
| Complete chain recall | 11/17 (64.7%) |
| Valid ledgers | 3/7 |
| Exact evidence coverage | 189/189 (100.0%) |
| Corrective apps | 7/7 |
| Transient retry apps | 1/7 |
| Safety clean apps | 3/7 |
| Hygiene passed apps | 7/7 |
| Discovery complete apps | 7/7 |
| Average focus coverage | 100.0% |

## Observability

| Metric | Value |
|---|---:|
| Requests | 271 |
| Errors | 0 |
| Input tokens | 9911448 |
| Output tokens | 422233 |
| Total tokens | 10333681 |
| Cost | $1.3565 |
| LLM wall time | 1h |

## Per-App Results

| App | Lang | Components | Chains | Ledger | Evidence | Discovery | Attempts | Correction | Retry |
|---|---|---:|---:|---|---:|---|---:|---|---|
| app-01 | Python | 2/7 (28.6%) | 0/3 (0.0%) | no | 32/32 | complete | 3 | yes | yes |
| app-05 | Python | 5/7 (71.4%) | 1/3 (33.3%) | yes | 24/24 | complete | 2 | yes | no |
| app-06 | Java | 6/6 (100.0%) | 3/3 (100.0%) | no | 29/29 | complete | 2 | yes | no |
| app-07 | Java | 5/6 (83.3%) | 1/2 (50.0%) | no | 22/22 | complete | 2 | yes | no |
| app-10 | Java | 6/6 (100.0%) | 2/2 (100.0%) | yes | 24/24 | complete | 2 | yes | no |
| app-11 | TypeScript | 3/3 (100.0%) | 1/1 (100.0%) | yes | 26/26 | complete | 2 | yes | no |
| app-14 | TypeScript | 6/6 (100.0%) | 3/3 (100.0%) | no | 32/32 | complete | 2 | yes | no |

## Notes

- Counts are aggregate evaluation metrics from sanitized benchmark summaries.
- Raw logs, generated app reports, temporary workspaces, and private scoring files are not copied here.
