# gpt-5.4-mini Evaluation

- Stamp: `20260528-224739`
- Apps scanned: 7
- Run status: complete

## Summary

| Metric | Value |
|---|---:|
| Component recall | 22/41 (53.7%) |
| Complete chain recall | 5/17 (29.4%) |
| Valid ledgers | 6/7 |
| Exact evidence coverage | 149/149 (100.0%) |
| Corrective apps | 3/7 |
| Transient retry apps | 0/7 |
| Safety clean apps | 7/7 |
| Hygiene passed apps | 7/7 |
| Discovery complete apps | 5/7 |
| Average focus coverage | 87.5% |

## Observability

| Metric | Value |
|---|---:|
| Requests | 61 |
| Errors | 0 |
| Input tokens | 1329483 |
| Output tokens | 56125 |
| Total tokens | 1385608 |
| Cost | $1.2463 |
| LLM wall time | 6m 37s |

## Per-App Results

| App | Lang | Components | Chains | Ledger | Evidence | Discovery | Attempts | Correction | Retry |
|---|---|---:|---:|---|---:|---|---:|---|---|
| app-01 | Python | 2/7 (28.6%) | 0/3 (0.0%) | yes | 18/18 | complete | 2 | yes | no |
| app-05 | Python | 5/7 (71.4%) | 1/3 (33.3%) | yes | 28/28 | partial | 1 | no | no |
| app-06 | Java | 0/6 (0.0%) | 0/3 (0.0%) | yes | 16/16 | complete | 2 | yes | no |
| app-07 | Java | 4/6 (66.7%) | 0/2 (0.0%) | yes | 16/16 | complete | 1 | no | no |
| app-10 | Java | 3/6 (50.0%) | 1/2 (50.0%) | yes | 16/16 | complete | 1 | no | no |
| app-11 | TypeScript | 3/3 (100.0%) | 1/1 (100.0%) | yes | 20/20 | complete | 1 | no | no |
| app-14 | TypeScript | 5/6 (83.3%) | 2/3 (66.7%) | no | 35/35 | partial | 2 | yes | no |

## Notes

- Counts are aggregate evaluation metrics from sanitized benchmark summaries.
- Raw logs, generated app reports, temporary workspaces, and private scoring files are not copied here.
