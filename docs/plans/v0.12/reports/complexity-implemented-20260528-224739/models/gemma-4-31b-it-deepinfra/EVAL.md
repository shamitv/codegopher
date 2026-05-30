# google/gemma-4-31B-it:deepinfra Evaluation

- Stamp: `20260528-224739`
- Apps scanned: 7
- Run status: complete

## Summary

| Metric | Value |
|---|---:|
| Component recall | 22/41 (53.7%) |
| Complete chain recall | 4/17 (23.5%) |
| Valid ledgers | 5/7 |
| Exact evidence coverage | 91/92 (98.9%) |
| Corrective apps | 6/7 |
| Transient retry apps | 0/7 |
| Safety clean apps | 7/7 |
| Hygiene passed apps | 7/7 |
| Discovery complete apps | 3/7 |
| Average focus coverage | 84.6% |

## Observability

| Metric | Value |
|---|---:|
| Requests | 171 |
| Errors | 0 |
| Input tokens | 2489313 |
| Output tokens | 58814 |
| Total tokens | 2548127 |
| Cost | $0.3460 |
| LLM wall time | 1h 16m |

## Per-App Results

| App | Lang | Components | Chains | Ledger | Evidence | Discovery | Attempts | Correction | Retry |
|---|---|---:|---:|---|---:|---|---:|---|---|
| app-01 | Python | 1/7 (14.3%) | 0/3 (0.0%) | yes | 14/14 | complete | 2 | yes | no |
| app-05 | Python | 4/7 (57.1%) | 1/3 (33.3%) | yes | 16/16 | partial | 2 | yes | no |
| app-06 | Java | 4/6 (66.7%) | 1/3 (33.3%) | no | 12/13 | complete | 2 | yes | no |
| app-07 | Java | 4/6 (66.7%) | 0/2 (0.0%) | yes | 14/14 | partial | 2 | yes | no |
| app-10 | Java | 5/6 (83.3%) | 1/2 (50.0%) | yes | 13/13 | complete | 2 | yes | no |
| app-11 | TypeScript | 1/3 (33.3%) | 0/1 (0.0%) | no | 9/9 | partial | 2 | yes | no |
| app-14 | TypeScript | 3/6 (50.0%) | 1/3 (33.3%) | yes | 13/13 | partial | 1 | no | no |

## Notes

- Counts are aggregate evaluation metrics from sanitized benchmark summaries.
- Raw logs, generated app reports, temporary workspaces, and private scoring files are not copied here.
