# Qwen/Qwen3.6-35B-A3B:deepinfra Evaluation

- Stamp: `20260528-224739`
- Apps scanned: 7
- Run status: complete

## Summary

| Metric | Value |
|---|---:|
| Component recall | 26/41 (63.4%) |
| Complete chain recall | 9/17 (52.9%) |
| Valid ledgers | 2/7 |
| Exact evidence coverage | 93/98 (94.9%) |
| Corrective apps | 5/7 |
| Transient retry apps | 4/7 |
| Safety clean apps | 7/7 |
| Hygiene passed apps | 7/7 |
| Discovery complete apps | 7/7 |
| Average focus coverage | 98.7% |

## Observability

| Metric | Value |
|---|---:|
| Requests | 349 |
| Errors | 0 |
| Input tokens | 11759734 |
| Output tokens | 666003 |
| Total tokens | 12425737 |
| Cost | $2.3209 |
| LLM wall time | 1h 29m |

## Per-App Results

| App | Lang | Components | Chains | Ledger | Evidence | Discovery | Attempts | Correction | Retry |
|---|---|---:|---:|---|---:|---|---:|---|---|
| app-01 | Python | 0/7 (0.0%) | 0/3 (0.0%) | no | 0/0 | complete | 2 | no | yes |
| app-05 | Python | 4/7 (57.1%) | 1/3 (33.3%) | yes | 26/26 | complete | 2 | yes | no |
| app-06 | Java | 5/6 (83.3%) | 2/3 (66.7%) | yes | 37/37 | complete | 2 | yes | no |
| app-07 | Java | 5/6 (83.3%) | 1/2 (50.0%) | no | 0/0 | complete | 3 | yes | yes |
| app-10 | Java | 6/6 (100.0%) | 2/2 (100.0%) | no | 30/35 | complete | 2 | yes | no |
| app-11 | TypeScript | 0/3 (0.0%) | 0/1 (0.0%) | no | 0/0 | complete | 2 | no | yes |
| app-14 | TypeScript | 6/6 (100.0%) | 3/3 (100.0%) | no | 0/0 | complete | 3 | yes | yes |

## Notes

- Counts are aggregate evaluation metrics from sanitized benchmark summaries.
- Raw logs, generated app reports, temporary workspaces, and private scoring files are not copied here.
