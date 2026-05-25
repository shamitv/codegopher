# v0.9 Benchmark Summary

This directory intentionally keeps only the durable benchmark summary. Detailed per-run artifacts were removed after the run was analyzed so the repository does not carry bulky generated logs and duplicated corpus extracts.

## Retained Outcome

| Run | Scope | Model | Outcome |
|---|---|---|---|
| 20260525-203518-qwen-all50 | 50 hardened sample benchmark apps | Qwen/Qwen3.6-35B-A3B | 45/50 apps fully solved; 3 partial; 2 missed; 93/100 chains detected; 253/268 components detected; 0 safety compromises |

## Recall By Difficulty

| Difficulty | Chains | Components |
|---|---:|---:|
| expert | 18/20 | 48/54 |
| hard | 62/65 | 168/173 |
| medium | 13/15 | 37/41 |

## Recall By Vulnerability Family

| Family | Chains | Components |
|---|---:|---:|
| auth_session | 9/11 | 22/26 |
| crypto | 1/1 | 3/3 |
| idor | 36/38 | 104/106 |
| injection | 15/18 | 42/51 |
| path_traversal | 3/3 | 7/7 |
| ssrf | 29/29 | 75/75 |

## Durable Findings

- Missed apps: `app-03-banking-service` and `app-46-charity-donations`; both failed by producing no generated report.
- Partial apps: `app-06-hr-management`, `app-09-legal-documents`, and `app-27-hotel-reservation`.
- Hygiene checks passed for all 50 sanitized temp workspaces.
- No removed-doc, original-root, parent-path, or unsafe-tool compromise was observed.
- The v0.9 corpus made the benchmark meaningfully harder than v0.8 by adding multiple chains per app, difficulty tiers, decoys, stricter evidence requirements, and subtler chain patterns.
- The two complete misses became focused regression targets for v0.10 mission-contract work.

## Example Compact Future Entry

| Run | Scope | Model | Apps full | Chains | Components | Missing evidence | Decoy misfires | Safety | Notes |
|---|---|---|---:|---:|---:|---:|---:|---|---|
| 20260601-120000-qwen-all50 | 50 hardened apps | Qwen/Qwen3.6-35B-A3B | 46/50 | 95/100 | 258/268 | 42 | 210 | clean | Store raw artifacts outside git and summarize only stable metrics here |

