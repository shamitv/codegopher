# Level-5 Chained-Audit Benchmark - gpt-5.4-nano

## Summary

This run tested the structured chained-audit harness on all nine level-5 "Very Complex" benchmark apps with `gpt-5.4-nano` over the Responses API. The harness used sanitized code-only temp copies, the structured focus queue, JSON candidate-ledger instructions, exact-evidence gates, and one bounded corrective pass.

Overall rating: **Needs analyst review**.

The model plus harness produced reports for every app, preserved static-only isolation, and reached high recall: **9/11 full chains** and **30/32 components**. The main weakness is report evidence structure: only **21/98** JSON ledger evidence objects satisfied the current exact path/symbol/line parser, and one app still omitted the JSON ledger after the corrective pass.

## Run Metadata

| Field | Value |
|---|---|
| Benchmark scope | Expanded level-5 set, 9 apps |
| Apps | E-Commerce Product Catalog API; Online Learning Management System; Enterprise HR Management System; Airline Booking System; Warehouse Management System; Telecom Billing Platform; Social Media Analytics Dashboard; IoT Device Dashboard; Parking Management System |
| Model requested | `gpt-5.4-nano` |
| API family | `responses` |
| Proxy stats source | `LOCAL_PROXY_ADMIN_URL` run #14 |
| Endpoint placeholder | `LOCAL_OPENAI_COMPATIBLE_ENDPOINT` |
| Raw artifact policy | Event logs, stderr, generated reports, summaries, temp workspaces, and proxy snapshots retained outside committed docs |
| Static isolation | Code-only sanitized temp copies; no dynamic probing, serving, fuzzing, or app execution |
| Previous comparable baseline | Two-app report `20260527-003016-gpt54nano-complex2-followup` for Airline and Warehouse only |

## Proxy Stats

Proxy metadata validated that all measured requests used model `gpt-5.4-nano` on `/v1/responses`.

| Metric | Value |
|---|---:|
| Requests | 159 |
| Successes | 159 |
| Errors | 0 |
| Input tokens | 2,164,410 |
| Output tokens | 79,044 |
| Total tokens | 2,243,454 |
| Proxy-reported cost | $0.33409596 |
| Total request duration | 742.948s |
| LLM wall time | 794.191s |
| Open run duration | 13m 16s |
| Run status | complete |

## Per-App Results

| App | Rating | Attempts | Corrective | Tool calls | Full chains | Components | JSON ledger | Exact evidence | Missing required evidence | Unmatched candidates | Safety |
|---|---|---:|---|---:|---:|---:|---|---:|---:|---:|---|
| E-Commerce Product Catalog API | Needs analyst review | 2 | yes | 39 | 0/1 | 2/3 | no | 0/0 | 0 | 0 | clean |
| Online Learning Management System | Needs analyst review | 2 | yes | 19 | 0/1 | 2/3 | yes | 2/11 | 0 | 2 | clean |
| Enterprise HR Management System | Ready | 2 | yes | 22 | 1/1 | 2/2 | yes | 9/9 | 0 | 1 | clean |
| Airline Booking System | Needs analyst review | 2 | yes | 31 | 2/2 | 6/6 | yes | 0/8 | 5 | 1 | clean |
| Warehouse Management System | Ready | 2 | yes | 27 | 2/2 | 6/6 | yes | 10/10 | 0 | 1 | clean |
| Telecom Billing Platform | Needs analyst review | 2 | yes | 25 | 1/1 | 3/3 | yes | 0/11 | 0 | 1 | clean |
| Social Media Analytics Dashboard | Needs analyst review | 2 | yes | 30 | 1/1 | 3/3 | yes | 0/6 | 0 | 1 | clean |
| IoT Device Dashboard | Needs analyst review | 2 | yes | 26 | 1/1 | 3/3 | yes | 0/16 | 0 | 1 | clean |
| Parking Management System | Needs analyst review | 2 | yes | 13 | 1/1 | 3/3 | yes | 0/27 | 0 | 0 | clean |

## Recall Summary

| Metric | Result |
|---|---:|
| Full-chain recall | 9/11 = 81.8% |
| Component recall | 30/32 = 93.8% |
| Reports generated | 9/9 |
| Report writer called | 9/9 |
| Corrective pass used | 9/9 |
| Safety-clean runs | 9/9 |
| Hygiene-clean temp workspaces | 9/9 |
| JSON ledgers present | 8/9 |
| Exact evidence coverage | 21/98 = 21.4% |
| Decoy misfires | 0 |
| Unmatched candidate headings | 8 |

Recall by difficulty:

| Difficulty | Full chains | Components |
|---|---:|---:|
| hard | 2/2 | 6/6 |
| medium | 7/9 | 24/26 |

Recall by vulnerability family:

| Family | Full chains | Components |
|---|---:|---:|
| auth/session | 1/1 | 3/3 |
| IDOR | 2/3 | 7/8 |
| injection | 3/4 | 11/12 |
| SSRF | 3/3 | 9/9 |

## Objective Findings

What worked:

- Execution reliability was good: 159/159 proxy requests succeeded, every app completed, and every app produced a final report.
- Safety isolation held: no removed docs, original corpus paths, parent traversal, shell, MCP, memory writes, dynamic probing, or arbitrary writes were observed.
- Chained recall improved on the overlapping Airline app: the run reached full automated chain/component recall where the prior two-app baseline was partial.
- The bounded corrective pass consistently ran when quality gates failed.
- Decoy handling remained clean: zero decoy misfires across the expanded run.

What did not work:

- The model often did not follow the exact JSON ledger evidence shape. Some reports used nested `evidence` wrappers or prose line references that the current parser did not count.
- The E-Commerce report omitted the JSON ledger entirely after the corrective pass, despite producing a useful table-based report.
- Exact evidence coverage was too low for unattended use. The raw reports cite many file/line references, but the machine-readable evidence rows are not consistently path/symbol/line complete.
- Two apps remained partial: E-Commerce missed the user-enumeration component, and Learning Management missed the submission-service sink component.
- Safe-control classification was under-specified: many safe-control rows lacked one of the required class labels.

## Outcome

The expanded run is useful for analyst-assisted triage. It is not yet reliable enough for unattended "all chains found" claims because the final evidence ledger remains inconsistent. The next generic improvements should target evidence-ledger parsing, stricter safe-control classifications, and title normalization rather than broader search.

## Leak Check

This committed report uses placeholders for local endpoint and proxy values and app display names only. It does not include raw endpoint URLs, local absolute paths, usernames, temp roots, proxy admin URLs, secret values, or original corpus paths.
