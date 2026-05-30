# gpt-5.4-nano Evaluation

- Stamp: `20260528-224739`
- Apps scanned: 7
- Run status: complete

## Summary

| Metric | Value |
|---|---:|
| Component recall | 11/41 (26.8%) |
| Complete chain recall | 2/17 (11.8%) |
| Valid ledgers | 6/7 |
| Exact evidence coverage | 99/99 (100.0%) |
| Corrective apps | 6/7 |
| Transient retry apps | 0/7 |
| Safety clean apps | 7/7 |
| Hygiene passed apps | 7/7 |
| Discovery complete apps | 4/7 |
| Average focus coverage | 79.7% |

## Observability

| Metric | Value |
|---|---:|
| Requests | 121 |
| Errors | 0 |
| Input tokens | 3046122 |
| Output tokens | 64486 |
| Total tokens | 3110608 |
| Cost | $0.6880 |
| LLM wall time | 11m 1s |

## Per-App Results

| App | Lang | Components | Chains | Ledger | Evidence | Discovery | Attempts | Correction | Retry |
|---|---|---:|---:|---|---:|---|---:|---|---|
| app-01 | Python | 2/7 (28.6%) | 0/3 (0.0%) | yes | 13/13 | partial | 2 | yes | no |
| app-05 | Python | 1/7 (14.3%) | 0/3 (0.0%) | yes | 25/25 | complete | 2 | yes | no |
| app-06 | Java | 2/6 (33.3%) | 0/3 (0.0%) | yes | 11/11 | partial | 1 | no | no |
| app-07 | Java | 0/6 (0.0%) | 0/2 (0.0%) | yes | 12/12 | complete | 2 | yes | no |
| app-10 | Java | 3/6 (50.0%) | 1/2 (50.0%) | yes | 17/17 | complete | 2 | yes | no |
| app-11 | TypeScript | 0/3 (0.0%) | 0/1 (0.0%) | yes | 8/8 | partial | 2 | yes | no |
| app-14 | TypeScript | 3/6 (50.0%) | 1/3 (33.3%) | no | 13/13 | complete | 2 | yes | no |

## Notes

- Counts are aggregate evaluation metrics from sanitized benchmark summaries.
- Raw logs, generated app reports, temporary workspaces, and private scoring files are not copied here.
