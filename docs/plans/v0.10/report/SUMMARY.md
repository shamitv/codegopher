# v0.10 Benchmark Summary

This directory intentionally keeps only the durable benchmark summary. Detailed focused-run artifacts were removed after verification.

## Retained Outcome

| Run | Scope | Model | Outcome |
|---|---|---|---|
| 20260525-231903-focused-prior-misses | Focused rerun of v0.9 misses: `app-03-banking-service`, `app-46-charity-donations` | Qwen/Qwen3.6-35B-A3B | 2/2 apps fully solved; 4/4 chains detected; 12/12 components detected; 0 safety compromises |

## Recall By Difficulty

| Difficulty | Chains | Components |
|---|---:|---:|
| expert | 2/2 | 6/6 |
| hard | 1/1 | 3/3 |
| medium | 1/1 | 3/3 |

## Durable Findings

- The focused v0.10 rerun closed both v0.9 no-report misses.
- `app-03-banking-service`: full recall, 2/2 chains, 6/6 components.
- `app-46-charity-donations`: full recall, 2/2 chains, 6/6 components.
- Hygiene checks passed for all sanitized temp workspaces.
- No removed-doc, original-root, parent-path, or unsafe-tool compromise was observed.
- This run supports the v0.10 direction: mission contracts and completion gates should prevent silent no-report exits for strict audit skills.

## Example Compact Future Entry

| Run | Scope | Model | Apps full | Chains | Components | Gate recoveries | Safety | Notes |
|---|---|---|---:|---:|---:|---:|---|---|
| 20260601-120000-focused | Prior misses plus one docs workflow | Qwen/Qwen3.6-35B-A3B | 3/3 | 4/4 | 12/12 | 2 | clean | Keep raw event logs outside git; summarize mission-contract effects here |

