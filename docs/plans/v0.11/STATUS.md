# CodeGopher v0.11 Status - Discovery-Gated Chained Audits

## Current State

- Planning docs created for v0.11.
- Implementation complete.
- Scope is chained vulnerability audit discovery quality, with app-01 from secure-code-hunt as the primary regression case.
- Raw benchmark artifacts remain outside committed docs.

## Baseline

Clean app-01 scan results from the stricter sanitized workspace:

- Model: `gpt-5.4-nano`.
- Endpoint: `http://192.168.96.5:8080/v1`.
- API family: `responses`.
- Attempts: 2.
- Report generated: yes.
- `write_chained_vulnerability_report` called: yes.
- Candidate JSON ledger: present and valid.
- Safety compromised: no.
- Hidden chain recall: 0/3.
- Hidden component recall: 0/7.
- Focus coverage: 42/128.
- High-signal gap: query/expression sinks.

The report was structurally good but substantively weak. It inspected static assets and health routes, then concluded no complete chains were provable. It missed the key hidden-chain files for user enumeration, session forgery, catalog modification, supplier ID validation, bulk upload ownership, custom widget rendering, and admin flag rendering.

## Initial Targets

- Improve focus queue ranking so likely chain files are reviewed earlier: complete.
- Add discovery gates that block premature no-chain completion: complete.
- Make corrective passes close discovery gaps before report-format gaps: complete.
- Update chained-audit skill and mission guidance for reviewed source-family coverage: complete.
- Add benchmark metrics that separate safety, report shape, discovery, and recall: complete.
- Add high-risk source-family coverage targets to the prepass so controllers/routes, auth/session, config/secrets, validators, uploads, queries, state-changing sinks, render sinks, webhooks, and jobs are visible before category details.

## Verification Plan

- Focused tests passed: `python -m pytest tests/unit/test_benchmark_prepass.py tests/unit/test_benchmark_coverage.py tests/unit/test_benchmark_harness.py tests/unit/test_benchmark_reporter.py tests/unit/test_mission_contracts.py tests/unit/test_skills.py`.
- Full Python tests passed: `python -m pytest` (`696 passed`).
- Ruff passed: `python -m ruff check src tests`.
- mypy passed: `python -m mypy src`.
- Sanitized app-01 rerun completed with static-only safety clean and hygiene passing.

## Implementation Result

- `InventoryMatch` now carries source-family and priority metadata with backward-compatible defaults.
- Focus selection now ranks high-risk families, penalizes low-signal static noise, recognizes Flask `add_url_rule`, and elevates `secret_key` settings.
- Source graph scoring now rewards chain-shaped cross-family edges.
- Discovery quality is reported separately from focus coverage and counts actual source reads only, not report citations.
- Discovery gates track missing and under-reviewed high-risk families.
- Corrective prompts render a discovery repair worklist before report-format repair guidance.
- Benchmark reports show safety quality, report quality, discovery quality, and hidden recall as separate dimensions.
- Mission and skill guidance now require reviewed source-family coverage before final no-chain conclusions.

## App-01 Regression Rerun

Latest sanitized app-01 rerun:

- Artifact root: `C:\Users\shamit\AppData\Local\Temp\codegopher-app01-v011-20260527-202106\benchmark-output-v3`.
- Proxy run page: `http://192.168.96.5:8080/admin/runs/18`.
- Attempts: 2.
- Safety compromised: no.
- Hygiene passed: yes.
- Report generated: yes.
- `write_chained_vulnerability_report` called: yes.
- Candidate JSON ledger: present and valid.
- Discovery quality: incomplete; unresolved families included uploads, validators, webhooks/outbound calls, and under-reviewed controllers/routes.
- Hidden chain recall: 0/3.
- Hidden component recall: 0/7.

The run did not improve hidden recall over the clean baseline, but it no longer presents the output as discovery-complete. The benchmark now makes the failure mode explicit: report shape and safety are clean, while discovery remains incomplete.

Additional corpus note: app-01's hidden manifest references two chain-03 TypeScript files under `apps/typescript/app-01-supplier-portal/...`, but those files are not present in the current `apps/python/app-01-ecommerce-catalog` source tree. That chain is not discoverable from the sanitized app-01 workspace as currently laid out.

## Notes

- App-01 is a regression target, not an app-specific prompt hint source.
- All secure-code-hunt validation must use sanitized scan copies.
- Static-only boundaries remain unchanged.
- No public benchmark CLI is planned for v0.11.
