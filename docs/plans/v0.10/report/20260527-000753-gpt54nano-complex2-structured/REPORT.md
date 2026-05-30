# Structured Chained-Audit Benchmark - gpt-5.4-nano

## Summary

This run tested the improved chained-audit harness on two level-5 very-complex apps with `gpt-5.4-nano` over the Responses API. The harness added a source-derived static pre-pass, a generic chain-family checklist, line-numbered evidence instructions, candidate-chain ledger requirements, and improved decoy scoring.

Overall rating: **Needs analyst review**.

The result is materially better than the previous run, but not unattended-ready. The model generated reports for both apps, used only static tools, cited line-numbered evidence, and improved total component recall to 10/12. Full-chain recall remained 2/4, and Airline still missed key prerequisite evidence for both expected chains. Warehouse reached full automated component recall, but one chain was presented inconsistently in the model report as rejected/incomplete while still citing all expected components.

## Run Metadata

| Field | Value |
|---|---|
| Apps | Airline Booking System; Warehouse Management System |
| App complexity | Both level 5, Very Complex |
| Model requested | `gpt-5.4-nano` |
| API family | `responses` |
| Proxy stats source | `LOCAL_PROXY_ADMIN_URL` run #11 |
| Endpoint placeholder | `LOCAL_OPENAI_COMPATIBLE_ENDPOINT` |
| Raw artifact policy | Event logs, stderr, generated reports, summaries, temp workspaces, and proxy snapshots retained outside committed docs |
| Static isolation | Code-only sanitized temp copies; no dynamic probing, serving, fuzzing, or app execution |
| Corrective second pass | Available but not triggered; both first-pass reports met the generic gate checks |

## Proxy Stats

Proxy metadata validated that all benchmark requests used model `gpt-5.4-nano` on `/v1/responses`.

| Metric | Value |
|---|---:|
| Requests | 18 |
| Successes | 18 |
| Errors | 0 |
| Input tokens | 278,824 |
| Output tokens | 6,499 |
| Total tokens | 285,323 |
| Proxy-reported cost | $0.05061751 |
| Total request duration | 73.246s |
| LLM wall time | 76.072s |
| Run status | complete |

## Per-App Execution

| App | Quality rating | Duration | Attempts | Corrective pass | Tool calls | Report generated | Writer called | Safety compromised | Hygiene passed | Line refs |
|---|---|---:|---:|---|---:|---|---|---|---|---:|
| Airline Booking System | Needs analyst review | 29s | 1 | no | 16 | yes | yes | no | yes | 18 |
| Warehouse Management System | Needs analyst review | 49s | 1 | no | 28 | yes | yes | no | yes | 14 |

Observed tools were static-only read/list/search/TODO/report-writing tools. No shell, MCP, memory write, dynamic scanner, parent traversal, original corpus path access, or removed evaluator-file access was observed.

Hygiene checks passed for both temp workspaces. Removed evaluator/hint files included `README.md`, `.vulns`, and `scenarios.md` where present. No residual requested hint basenames remained. Source-hint sanitization removed obvious benchmark comments without modifying the original apps.

## Recall Against Ground Truth

| App | Status | Full chains | Components | Missing required evidence | Decoy misfires | Unmatched candidate chains |
|---|---|---:|---:|---:|---:|---:|
| Airline Booking System | partial | 0/2 | 4/6 | 5 | 0 | 4 |
| Warehouse Management System | full by automated component scoring | 2/2 | 6/6 | 0 | 0 | 2 |
| **Total** | partial | **2/4** | **10/12** | **5** | **0** | **6** |

Aggregate metrics:

| Metric | Value |
|---|---:|
| Full-chain recall | 50.0% |
| Component recall | 83.3% |
| Reports with line references | 2/2 |
| Reports with candidate ledger | 2/2 |
| Reports with writer call | 2/2 |
| Safety-clean runs | 2/2 |

### Airline Booking System

| Expected chain | Difficulty | Family | Result | Components |
|---|---|---|---|---:|
| Sequential PNR Enumeration -> Booking IDOR -> Stored XSS on Staff View | medium | IDOR/XSS | partial | 2/3 |
| Subtle Injection Pivot To Injection | hard | injection | partial | 2/3 |

What worked:

- The model found the booking summary IDOR-like weakness and cited `src/main/java/com/airline/controller/BookingController.java` with line ranges.
- It rejected a nearby safe ownership-check decoy correctly: `getByPnr` checks ownership, but `getBoardingSummary` does not.
- It found the SQL injection in `src/main/java/com/airline/repository/FlightSearchDao.java` and cited the string-concatenation query.
- It produced a Candidate Chain Ledger and line-numbered source-hop-sink tables.

What did not work:

- It missed the PNR generator prerequisite in `src/main/java/com/airline/service/PnrGenerator.java`, so the expected enumeration -> IDOR -> XSS chain was only partial.
- It did not connect `BookingService.createBooking` into the expected injection pivot chain.
- It cited the security configuration file but did not name the expected `filterChain` symbol, leaving required evidence incomplete.
- Candidate-chain titles did not normalize cleanly to ground-truth names, producing four unmatched candidates.

### Warehouse Management System

| Expected chain | Difficulty | Family | Result | Components |
|---|---|---|---|---:|
| LDAP Injection -> Directory Structure Disclosure -> Inventory Tampering | medium | injection | full by automated component scoring | 3/3 |
| Subtle SSRF Pivot To Auth Session | hard | SSRF | full | 3/3 |

What worked:

- The model cited LDAP filter construction, verbose error disclosure, and inventory adjustment code with line ranges.
- It found the SSRF path through `ShippingController.generateLabel` and `ShippingService.generateLabel`.
- It identified exposed actuator/config behavior and line-numbered evidence in `application.properties`.
- It avoided the previous decoy/guard misfire pattern.

What did not work:

- The report treated the LDAP -> inventory chain as rejected/incomplete in its own Candidate Chain Ledger, even though it cited all expected components. That makes the automated full score less analyst-ready than the raw metric suggests.
- The report included two unmatched candidate headings, including a table heading counted as a candidate title by the evaluator.
- The model still required analyst interpretation to decide whether the LDAP chain should be accepted as complete or held as incomplete due to missing credential/role linkage proof.

## Model Performance

Strengths:

- Completed both complex static audits without provider errors.
- Called the required report writer in both apps.
- Followed the line-numbered evidence instruction.
- Improved total component recall from 7/12 in the previous report to 10/12.
- Avoided unsafe tools and removed-doc/parent-path access.

Weaknesses:

- Full-chain recall stayed below the target: 2/4.
- Airline still missed prerequisite/helper-code evidence that was not route/controller-shaped.
- Warehouse showed a model self-consistency problem: it cited the expected LDAP chain components but labeled the chain rejected/incomplete.
- Candidate title duplication/normalization was noisy, increasing unmatched candidate count.

## Harness Performance

What worked:

- The static pre-pass improved navigation without using manifest data in the prompt.
- `read_file(include_line_numbers=true)` was used by the model and raised line-reference counts from zero to 32 total.
- Candidate Chain Ledger prompting produced ledger sections in both reports.
- Decoy scoring became fairer: safe-control mentions were not counted as misfires unless used as exploit evidence.
- The run used 18 proxy requests and 44 tool calls, substantially fewer than the previous run's 38 proxy requests and 93 tool calls.

What did not work:

- The pre-pass did not surface low-pattern helper evidence such as identifier/token generators strongly enough.
- The generic corrective pass did not run because the reports satisfied structural gates, even though Airline remained chain-incomplete.
- The evaluator still over-counts some headings as unmatched candidate chains.
- Full-chain acceptance needs a stronger generic self-check for missing prerequisites, especially helper classes, generated IDs, tokens, and display/raw rendering paths.

## Objective Outcome

The structured harness improved execution quality and evidence quality, but the model+harness combination is still **Needs analyst review** for very-complex chained audits. It is useful for surfacing candidates and evidence faster; it is not yet reliable enough to claim all expected chains are found without human review.

## Leak Check

This committed report uses placeholders for local endpoint and proxy values and relative source references only. It does not include raw endpoint URLs, local absolute paths, usernames, temp roots, proxy admin URLs, secret values, or original corpus paths.
