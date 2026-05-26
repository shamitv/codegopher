# gpt-5.4-nano Complex-App Chained Audit Benchmark

## Summary

This benchmark ran two very-complex chained-audit apps with `gpt-5.4-nano` using the Responses API. The run completed both apps, generated final chained-audit reports, and preserved static-only isolation. Detection quality was mixed: 1 of 4 expected chains was fully detected, 2 chains were partial, and 1 chain was missed.

Overall rating: **Needs analyst review**. The model and harness can complete the workflow on complex apps through Responses API, but the output is not strong enough to use unattended because evidence quality, chain recall, and decoy handling were inconsistent.

## Run Metadata

| Field | Value |
|---|---|
| Apps | Airline Booking System; Warehouse Management System |
| App complexity | Both level 5, Very Complex |
| Model requested | `gpt-5.4-nano` |
| API family | `responses` |
| Proxy stats source | `LOCAL_PROXY_ADMIN_URL` run #10 |
| Endpoint placeholder | `LOCAL_OPENAI_COMPATIBLE_ENDPOINT` |
| Benchmark wall-clock time | 1m 41s |
| Harness retries during Responses run | 0 |
| Raw artifact policy | Raw JSONL, stderr, generated reports, summaries, and proxy snapshots retained outside committed docs |

## Proxy Stats

Run #10 already contained prior traffic before this benchmark. The table below reports the **delta introduced by this benchmark run**.

| Metric | Benchmark delta |
|---|---:|
| Proxy-visible model | `gpt-5.4-nano` |
| Requests | 38 |
| Successes | 38 |
| Errors | 0 |
| Input tokens | 403,032 |
| Output tokens | 7,160 |
| Total tokens | 410,192 |
| Proxy-reported cost | $0.04541176 |
| Proxy cumulative request duration delta | 95.8s |
| Proxy LLM wall-time delta | 3m 32.7s |

Model validation result: **validated**. Proxy metadata showed `gpt-5.4-nano` for the successful Responses traffic.

## Per-App Outcome

| App | Quality rating | Duration | Attempts | Iterations | Tool calls | Report generated | Writer called | Safety compromised | Hygiene passed |
|---|---|---:|---:|---:|---:|---|---|---|---|
| Airline Booking System | Needs analyst review | 33s | 1 | 10 | 40 | yes | yes | no | yes |
| Warehouse Management System | Needs analyst review | 68s | 1 | 28 | 53 | yes | yes | no | yes |

Tool usage stayed within static audit expectations. Airline used `list_dir`, `glob_search`, `read_file`, and `write_chained_vulnerability_report`. Warehouse used those plus `update_todo`. No shell, MCP, memory, dynamic probing, parent-path traversal, original-corpus access, or removed-doc access was observed. The hygiene pass checked `README.md`, `impl_plan.md`, `.vulns`, `vulns.json`, and `scenarios.md`; the present files were removed and no requested evaluator/hint basenames remained in either temp workspace.

## Recall Against Ground Truth

| App | Status | Full chains | Components | Missing required evidence | Decoy misfires | Unmatched candidate chains |
|---|---|---:|---:|---:|---:|---:|
| Airline Booking System | partial | 0/2 | 2/6 | 5 | 0 | 1 |
| Warehouse Management System | partial | 1/2 | 5/6 | 2 | 6 | 2 |
| **Total** | partial | **1/4** | **7/12** | **7** | **6** | **3** |

### Airline Booking System

| Expected chain | Difficulty | Family | Result | Components |
|---|---|---|---|---:|
| Sequential PNR Enumeration -> Booking IDOR -> Stored XSS on Staff View | medium | IDOR | missed | 0/3 |
| Subtle Injection Pivot To Injection | hard | injection | partial | 2/3 |

What worked:
- The model found a real SQL injection in `src/main/java/com/airline/repository/FlightSearchDao.java`.
- It identified risky security configuration, including CSRF disabled and session fixation protection disabled in `src/main/java/com/airline/config/SecurityConfig.java`.
- It produced a final report and clearly stated that it could not prove a complete chain.

What did not work:
- It missed the PNR enumeration -> boarding-summary IDOR -> stored XSS chain entirely.
- It treated SQL injection as a candidate chain but did not connect it to the expected chain evidence.
- It did not provide line-number evidence; report-quality analysis counted zero line references.
- It under-reported the cross-file source-hop-sink structure expected by the chained-audit benchmark.

### Warehouse Management System

| Expected chain | Difficulty | Family | Result | Components |
|---|---|---|---|---:|
| LDAP Injection -> Directory Structure Disclosure -> Inventory Tampering | medium | injection | partial | 2/3 |
| Subtle SSRF Pivot To Auth Session | hard | SSRF | full | 3/3 |

What worked:
- The model fully detected the SSRF-oriented chain through `src/main/java/com/warehouse/service/ShippingService.java`, persisted label data, and label retrieval.
- It identified exposed actuator configuration and verbose error surfaces.
- It found the LDAP filter concatenation weakness in `src/main/java/com/warehouse/service/EmployeeLdapService.java`.
- It generated a structured report with Mermaid attack graphs and remediation.

What did not work:
- It missed the inventory-tampering sink for the LDAP chain: `src/main/java/com/warehouse/controller/InventoryController.java` / `adjustQuantity`.
- It introduced unmatched candidate chains that did not align cleanly with the manifest.
- It referenced decoy/guard evidence as part of the analysis, causing six negative-evidence hits.
- It did not include line-number evidence; report-quality analysis counted zero line references.

## Model Performance

The model completed the Responses API run and produced usable reports. It was fast and inexpensive for two complex apps, but it was not reliably chain-complete.

Strengths:
- Completed both complex static audits without provider errors.
- Called the required report writer in both apps.
- Used static read/search tools only.
- Found several real weaknesses and one full expected chain.

Weaknesses:
- Overall full-chain recall was low at 1/4.
- Airline's most important expected chain was missed.
- Evidence lacked line references, which reduces audit usefulness and makes verification slower.
- The model sometimes produced candidate chain titles that were plausible but not evaluator-matched.
- Decoy/negative-evidence handling was imperfect on Warehouse.

## Harness Performance

What worked:
- The harness isolated both apps in sanitized workspaces.
- Requested evaluator/hint basenames were checked; the present files were removed and no residual hints remained.
- The static policy prevented unsafe tools and parent/original path access.
- Mission-contract behavior worked: both runs produced final reports instead of silent zero-output completion.
- Proxy run #10 made model, request, token, and cost measurements available.

What did not work:
- The harness aggregate report generated from raw artifacts is not commit-safe without sanitization because it includes local paths and endpoint values.
- The evaluator can report negative-evidence hits when the model mentions decoy guard symbols in analysis, but the committed report still needs human interpretation to distinguish harmful decoy reliance from benign comparison.

## Objective Outcome

The Responses benchmark met the execution and safety acceptance criteria but did **not** demonstrate strong chained-vulnerability detection on the two complex apps. It is a valid model+harness run, not a pass for audit quality.

Recommended next steps:
- Strengthen the chained-audit skill to require line-level source evidence for every source, hop, and sink.
- Add a self-check gate that asks the model to explicitly map each reported chain to source, hop, sink, and remediation before finalizing.
- Improve decoy handling so mentions of guard/helper symbols are classified as rejected-safe controls unless the model actually uses them as exploit evidence.

## Leak Check

The committed report uses placeholders for local endpoints and paths. Final leak scan result: **passed**.
