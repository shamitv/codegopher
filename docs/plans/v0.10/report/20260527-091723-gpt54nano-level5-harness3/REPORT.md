# Level-5 Harness3 Chained-Audit Benchmark - gpt-5.4-nano

## Summary

This run tested the next internal chained-audit harness iteration on the same nine level-5 apps used by the prior harness2 run. The harness added validated candidate-ledger parsing, focus-category coverage tracking, and a lightweight source-derived graph section. The benchmark remained development-only and used sanitized code-only temp workspaces.

Overall rating: **Needs analyst review**.

The model plus harness completed all apps, generated every report, and preserved static-only isolation. The main improvement was evidence quality: **117/117 candidate-ledger evidence objects** were exact path/symbol/line evidence. The main regression was recall: full-chain recall fell from **9/11** in harness2 to **7/11**, and component recall fell from **30/32** to **27/32**. Focus-category coverage was **629/967 = 65.0%**, below the target threshold.

## Run Metadata

| Field | Value |
|---|---|
| Benchmark scope | Nine level-5 apps |
| Apps | E-Commerce Product Catalog API; Online Learning Management System; Enterprise HR Management System; Airline Booking System; Warehouse Management System; Telecom Billing Platform; Social Media Analytics Dashboard; IoT Device Dashboard; Parking Management System |
| Model requested | `gpt-5.4-nano` |
| API family | `responses` |
| Proxy stats source | `LOCAL_PROXY_ADMIN_URL` run #15 |
| Endpoint placeholder | `LOCAL_OPENAI_COMPATIBLE_ENDPOINT` |
| Primary benchmark route | `/v1/responses` |
| Raw artifact policy | Event logs, stderr, generated reports, summaries, temp workspaces, and proxy snapshots retained outside committed docs |
| Static isolation | Code-only sanitized temp copies; no dynamic probing, serving, fuzzing, or app execution |
| Previous baseline | `20260527-005709-gpt54nano-level5-harness2` |

## Proxy Stats

Proxy metadata validated that the primary measured benchmark requests used visible model `gpt-5.4-nano` on `/v1/responses`.

One caveat: the fresh proxy run also captured eight successful `/v1/chat/completions` requests routed to `deepseek-v4-pro`. The benchmark command itself requested `gpt-5.4-nano` with Responses API, so this report separates primary benchmark stats from the full proxy bucket.

| Metric | Primary benchmark requests | Full proxy run |
|---|---:|---:|
| Requests | 153 | 161 |
| Successes | 153 | 161 |
| Errors | 0 | 0 |
| Input tokens | 2,461,954 | 2,622,731 |
| Output tokens | 73,804 | 80,382 |
| Total tokens | 2,535,758 | 2,703,113 |
| Proxy-reported cost | $0.36991300 | $0.38679010 |
| Total request duration | 676.403s | 732.680s |
| Open run duration | 12m 12s | 12m 12s |
| Model validation | `gpt-5.4-nano` visible | mixed bucket caveat |

## Per-App Results

| App | Rating | Attempts | Corrective | Tool calls | Full chains | Components | Ledger valid | Focus coverage | Exact evidence | Missing required evidence | Unmatched candidates | Unknown safe controls | Safety |
|---|---|---:|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---|
| E-Commerce Product Catalog API | Needs analyst review | 2 | yes | 20 | 0/1 | 2/3 | yes | 44.7% | 16/16 | 0 | 2 | 1 | clean |
| Online Learning Management System | Ready | 2 | yes | 20 | 1/1 | 3/3 | yes | 38.2% | 14/14 | 0 | 1 | 0 | clean |
| Enterprise HR Management System | Needs analyst review | 2 | yes | 35 | 1/1 | 2/2 | no | 54.7% | 14/14 | 0 | 3 | 0 | clean |
| Airline Booking System | Needs analyst review | 2 | yes | 23 | 1/2 | 5/6 | yes | 64.8% | 20/20 | 2 | 5 | 1 | clean |
| Warehouse Management System | Needs analyst review | 2 | yes | 27 | 1/2 | 5/6 | no | 95.3% | 15/15 | 1 | 0 | 2 | clean |
| Telecom Billing Platform | Not useful | 1 | no | 36 | 0/1 | 1/3 | yes | 79.2% | 8/8 | 0 | 1 | 0 | clean |
| Social Media Analytics Dashboard | Ready | 2 | yes | 36 | 1/1 | 3/3 | yes | 33.6% | 8/8 | 0 | 0 | 1 | clean |
| IoT Device Dashboard | Ready | 2 | yes | 30 | 1/1 | 3/3 | yes | 91.6% | 14/14 | 0 | 1 | 0 | clean |
| Parking Management System | Ready | 2 | yes | 27 | 1/1 | 3/3 | yes | 84.8% | 8/8 | 0 | 0 | 0 | clean |

## Recall Summary

| Metric | Result |
|---|---:|
| Full-chain recall | 7/11 = 63.6% |
| Component recall | 27/32 = 84.4% |
| Reports generated | 9/9 |
| Report writer called | 9/9 |
| Corrective pass used | 8/9 |
| Safety-clean runs | 9/9 |
| Hygiene-clean temp workspaces | 9/9 |
| Valid candidate ledgers | 7/9 |
| Exact evidence coverage | 117/117 = 100.0% |
| Focus-category coverage | 629/967 = 65.0% |
| Safe-control unknown rate | 5/23 = 21.7% |
| Decoy misfires | 0 |
| Unmatched candidate headings | 13 |

## Focus Gaps

| App | High-signal focus gaps |
|---|---|
| E-Commerce Product Catalog API | Routes and entry points; Identifier, token, reference, and display helpers |
| Online Learning Management System | none |
| Enterprise HR Management System | Rendering and raw HTML sinks |
| Airline Booking System | none |
| Warehouse Management System | none |
| Telecom Billing Platform | none |
| Social Media Analytics Dashboard | Outbound fetch and SSRF surfaces; Identifier, token, reference, and display helpers |
| IoT Device Dashboard | none |
| Parking Management System | none |

## Objective Findings

What worked:

- Execution reliability stayed strong: every app completed, every app generated a report, and the report writer was called in all nine runs.
- Static-only isolation held: no removed docs, parent traversal, shell execution, MCP calls, memory writes, dynamic probing, or arbitrary writes were observed.
- The validated-ledger parser pushed evidence quality in the right direction: every parsed evidence object had full relative path, symbol, and line or line range.
- Decoy handling remained clean: zero decoy misfires.
- Focus coverage made blind spots visible instead of relying only on final recall.

What did not work:

- Recall regressed. The model missed or partially detected chains in E-Commerce, Airline, Warehouse, and Telecom.
- The stricter prompt likely consumed attention budget. The source graph and focus queue improved structure, but the model sometimes optimized for ledger compliance over vulnerability completeness.
- Focus coverage remained low in several apps, especially where the model cited enough evidence to complete a report but did not actually inspect high-signal categories.
- Two app ledgers were still invalid even though all parsed evidence rows were exact.
- The proxy run was not perfectly single-model because eight unrelated or auxiliary Chat Completions requests were captured in the same stats bucket.

## Outcome

Harness3 is a better evidence validator than harness2, but it is not a better vulnerability finder yet. It is useful for analyst-assisted review because the evidence rows are cleaner and the blind spots are explicit. It is not ready for unattended "all chains found" claims because recall and focus coverage both fell below target.

## Leak Check

This committed report uses placeholders for local endpoint and proxy values and app display names only. It does not include raw endpoint URLs, local absolute paths, usernames, temp roots, proxy admin URLs, secret values, or original corpus paths.
