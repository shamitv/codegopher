# CodeGopher v0.9 Status - Harder Chained Benchmark Corpus

## Implementation State

- v0.9 plan and TODO docs created.
- Internal benchmark manifests now support multiple chains plus `difficulty`, `subtlety_tags`, `required_evidence`, `chain_prerequisites`, `negative_evidence`, and `vulnerability_family`.
- Evaluator now reports full-chain recall, component recall, missing required evidence, decoy/negative-evidence hits, recall by difficulty, and recall by vulnerability family.
- Aggregate benchmark reports now include grouped difficulty/family recall plus per-app missing-evidence and decoy-misfire counts.
- All 50 sample benchmark apps were upgraded in place with v0.9 manifest metadata, 100 total chains, 268 total components, and one neutral guard/helper decoy file per app.

## Corpus Inventory

- Apps: 50.
- Chains: 100.
- Components: 268.
- Difficulty split: 15 medium apps, 25 hard apps, 10 expert apps.
- Language split retained: Python, Java, JavaScript, and TypeScript apps remain in their original stacks.
- Sanitized temp-copy hygiene validation passed across all 50 apps.

## Validation

- Manifest parse and anchor validation: passed for all 50 apps.
- Temp-copy hygiene validation: 50/50 passed; 4,764 evaluator files removed from copied workspaces; 190 source hint lines sanitized in temp copies; 0 residual hints.
- Focused benchmark tests: passed.
- Full Python test suite: 651 passed.
- Ruff: passed.
- Mypy: passed.

## Real Qwen Benchmark

- Report: `docs/plans/v0.9/report/20260525-203518-qwen-all50/REPORT.md`
- Model requested: `Qwen/Qwen3.6-35B-A3B`
- Proxy run: `LOCAL_PROXY_RUN_URL`
- Proxy route confirmation: 541/541 requests used request model `Qwen/Qwen3.6-35B-A3B`, upstream model `Qwen/Qwen3.6-35B-A3B:deepinfra`, and billing model `Qwen/Qwen3.6-35B-A3B:deepinfra`.
- Proxy stats for run 9 at inspection time: 541 requests, 5.9M total tokens, $1.30 reported cost, 0 HTTP errors.
- Benchmark attempts: 51 total attempts, 1 retry.
- Reports generated: 48/50.
- Safety: 0 compromised runs; hygiene passed 50/50.

## Benchmark Outcome

- App recall: 45 full, 3 partial, 2 missed.
- Full-chain recall: 93/100.
- Component recall: 253/268.

### Recall By Difficulty

| Difficulty | Chains | Components |
|---|---:|---:|
| medium | 13/15 | 37/41 |
| hard | 62/65 | 168/173 |
| expert | 18/20 | 48/54 |

### Recall By Family

| Family | Chains | Components |
|---|---:|---:|
| auth_session | 9/11 | 22/26 |
| crypto | 1/1 | 3/3 |
| idor | 36/38 | 104/106 |
| injection | 15/18 | 42/51 |
| path_traversal | 3/3 | 7/7 |
| ssrf | 29/29 | 75/75 |

## Missed Or Partial Apps

- `app-03-banking-service`: missed, 0/2 chains, 0/6 components, report missing.
- `app-06-hr-management`: partial, 1/2 chains, 5/6 components.
- `app-09-legal-documents`: partial, 1/2 chains, 4/5 components.
- `app-27-hotel-reservation`: partial, 1/2 chains, 4/5 components.
- `app-46-charity-donations`: missed, 0/2 chains, 0/6 components, report missing.

## Notes

- The v0.9 corpus is intentionally not directly comparable to v0.8 because the corpus changed in place and doubled the expected chain count.
- The current upgrade used structured manifest hardening, stricter evaluator scoring, and neutral source decoys across all apps. A future pass can make the source flows themselves more bespoke per app if the benchmark becomes easy again.
