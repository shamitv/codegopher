# google/gemma-4-26B-A4B-it:deepinfra Evaluation

- Stamp: `20260528-224739`
- Apps scanned: 7
- Run status: complete

## Summary

| Metric | Value |
|---|---:|
| Component recall | 16/41 (39.0%) |
| Complete chain recall | 4/17 (23.5%) |
| Valid ledgers | 4/7 |
| Exact evidence coverage | 59/59 (100.0%) |
| Corrective apps | 7/7 |
| Transient retry apps | 0/7 |
| Safety clean apps | 7/7 |
| Hygiene passed apps | 7/7 |
| Discovery complete apps | 3/7 |
| Average focus coverage | 81.4% |

## Observability

| Metric | Value |
|---|---:|
| Requests | 232 |
| Errors | 0 |
| Input tokens | 2893506 |
| Output tokens | 55154 |
| Total tokens | 2948660 |
| Cost | $0.2213 |
| LLM wall time | 31m 28s |

## Per-App Results

| App | Lang | Components | Chains | Ledger | Evidence | Discovery | Attempts | Correction | Retry |
|---|---|---:|---:|---|---:|---|---:|---|---|
| app-01 | Python | 0/7 (0.0%) | 0/3 (0.0%) | no | 4/4 | complete | 2 | yes | no |
| app-05 | Python | 3/7 (42.9%) | 1/3 (33.3%) | yes | 9/9 | partial | 2 | yes | no |
| app-06 | Java | 1/6 (16.7%) | 0/3 (0.0%) | yes | 13/13 | complete | 2 | yes | no |
| app-07 | Java | 3/6 (50.0%) | 1/2 (50.0%) | yes | 7/7 | partial | 2 | yes | no |
| app-10 | Java | 5/6 (83.3%) | 1/2 (50.0%) | no | 5/5 | complete | 2 | yes | no |
| app-11 | TypeScript | 1/3 (33.3%) | 0/1 (0.0%) | no | 8/8 | partial | 2 | yes | no |
| app-14 | TypeScript | 3/6 (50.0%) | 1/3 (33.3%) | yes | 13/13 | partial | 2 | yes | no |

## Notes

- Counts are aggregate evaluation metrics from sanitized benchmark summaries.
- Raw logs, generated app reports, temporary workspaces, and private scoring files are not copied here.
