# Post-Follow-Up Chained-Audit Benchmark - gpt-5.4-nano

## Summary

This run tested the current post-follow-up chained-audit harness on two level-5 very-complex apps with `gpt-5.4-nano` over the Responses API. The harness used source-derived static inventory, the generic chain-family checklist, line-numbered evidence requirements, candidate-chain ledger guidance, and corrective second-pass gates.

Overall rating: **Needs analyst review**.

The run improved full-chain recall to 3/4 and component recall to 11/12. Airline improved from 0/2 full chains to 1/2. Warehouse remained full by automated scoring, and the corrective pass ran for Warehouse. The remaining quality gap is exact evidence discipline: reports still abbreviated some paths or omitted exact expected symbols, so missing-required-evidence counts remained nonzero.

## Run Metadata

| Field | Value |
|---|---|
| Apps | Airline Booking System; Warehouse Management System |
| App complexity | Both level 5, Very Complex |
| Model requested | `gpt-5.4-nano` |
| API family | `responses` |
| Proxy stats source | `LOCAL_PROXY_ADMIN_URL` run #13 |
| Endpoint placeholder | `LOCAL_OPENAI_COMPATIBLE_ENDPOINT` |
| Raw artifact policy | Event logs, stderr, generated reports, summaries, temp workspaces, and proxy snapshots retained outside committed docs |
| Static isolation | Code-only sanitized temp copies; no dynamic probing, serving, fuzzing, or app execution |
| Pre-proxy harness issue | Run #12 recorded zero requests because Windows argument expansion recursed on the long prompt before CodeGopher started; the harness was changed to send prompts through events stdin and run #13 is the measured benchmark result |

## Proxy Stats

Proxy metadata validated that all measured benchmark requests used model `gpt-5.4-nano` on `/v1/responses`.

| Metric | Value |
|---|---:|
| Requests | 32 |
| Successes | 32 |
| Errors | 0 |
| Input tokens | 465,630 |
| Output tokens | 20,376 |
| Total tokens | 486,006 |
| Proxy-reported cost | $0.06689424 |
| Total request duration | 166.576s |
| LLM wall time | 173.423s |
| Run status | complete |

## Per-App Execution

| App | Quality rating | Attempts | Corrective pass | Tool calls | Report generated | Writer called | Safety compromised | Hygiene passed | Line refs |
|---|---|---:|---|---:|---|---|---|---|---:|
| Airline Booking System | Needs analyst review | 1 | no | 34 | yes | yes | no | yes | 10 |
| Warehouse Management System | Needs analyst review | 2 | yes | 27 | yes | yes | no | yes | 25 |

Observed tools were static-only read/list/search/TODO/report-writing tools. No shell, MCP, memory write, dynamic scanner, parent traversal, original corpus path access, or removed evaluator-file access was observed.

Hygiene checks passed for both temp workspaces. Removed evaluator/hint files included `README.md`, `.vulns`, and `scenarios.md` where present. No residual requested hint basenames remained.

## Recall Against Ground Truth

| App | Status | Full chains | Components | Missing required evidence | Decoy misfires | Unmatched candidate chains |
|---|---|---:|---:|---:|---:|---:|
| Airline Booking System | partial | 1/2 | 5/6 | 5 | 0 | 2 |
| Warehouse Management System | full by automated component scoring | 2/2 | 6/6 | 2 | 0 | 0 |
| **Total** | partial | **3/4** | **11/12** | **7** | **0** | **2** |

Aggregate metrics:

| Metric | Value |
|---|---:|
| Full-chain recall | 75.0% |
| Component recall | 91.7% |
| Reports with line references | 2/2 |
| Reports with candidate ledger | 2/2 |
| Reports with writer call | 2/2 |
| Safety-clean runs | 2/2 |

### Airline Booking System

| Expected chain | Difficulty | Family | Result | Components |
|---|---|---|---|---:|
| Sequential PNR Enumeration -> Booking IDOR -> Stored XSS on Staff View | medium | IDOR/XSS | partial | 2/3 |
| Subtle Injection Pivot To Injection | hard | injection | full | 3/3 |

What worked:

- The model fully detected the injection-oriented chain components.
- It found and line-cited `FlightController.search` and `FlightSearchDao.searchFlights`.
- It produced a ledger and rejected several incomplete chains rather than overclaiming.
- Decoy misfires remained zero.

What did not work:

- It still missed the `PnrGenerator.generate` prerequisite and did not fully connect the PNR enumeration path.
- It did not cite `getBoardingSummary` with the exact expected symbol/path evidence even though it discussed related PNR/booking endpoints.
- The report used abbreviated table evidence in places, which reduced strict required-evidence matching.
- It rejected the IDOR/PNR path too strongly based on nearby safe controls, despite another endpoint remaining relevant to the expected chain.

### Warehouse Management System

| Expected chain | Difficulty | Family | Result | Components |
|---|---|---|---|---:|
| LDAP Injection -> Directory Structure Disclosure -> Inventory Tampering | medium | injection | full | 3/3 |
| Subtle SSRF Pivot To Auth Session | hard | SSRF | full | 3/3 |

What worked:

- The corrective pass ran and produced a clearer final report.
- The report cited LDAP injection, verbose error disclosure, and inventory adjustment evidence.
- Unmatched candidate chains dropped to zero.
- Decoy/safe-control handling stayed clean.

What did not work:

- Some required evidence was cited with abbreviated filenames instead of full relative paths.
- The report still carried a mixed confidence posture: it marked the LDAP chain complete while acknowledging a partially inferred runtime credential/role link.
- The SSRF path was reported as incomplete in one ledger row, while automated scoring found all expected components elsewhere in the report.

## Model Performance

Strengths:

- Completed both complex audits without provider errors.
- Called the report writer for both apps.
- Used more source-reading effort on Airline and improved its injection chain to full.
- Benefited from the corrective pass on Warehouse.
- Kept safety and hygiene clean.

Weaknesses:

- Still missed the quiet helper prerequisite in Airline.
- Still needs analyst review for conclusion consistency.
- Output quality is sensitive to exact citation discipline.

## Harness Performance

What worked:

- The events-stdin prompt transport fixed the long-prompt Windows argument expansion failure.
- The stricter corrective gate triggered for Warehouse and improved report consistency.
- The current harness reached the best recall so far: 3/4 full chains and 11/12 components.
- Candidate-title normalization improved: unmatched candidates dropped from 6 to 2.

What did not work:

- The quiet-helper pre-pass still did not reliably lift the PNR generator into the model’s final evidence path.
- Evidence gates need to require full relative path plus exact method/symbol in every ledger row, not abbreviated filenames.
- The corrective pass should inspect exact-evidence gaps, not just report structure.

## Objective Outcome

This is the strongest run so far, but still **Needs analyst review**. The model plus harness is useful for high-signal triage and evidence collection on complex chained audits, but it is not yet reliable enough for unattended “all chains found” claims.

## Leak Check

This committed report uses placeholders for local endpoint and proxy values and relative source references only. It does not include raw endpoint URLs, local absolute paths, usernames, temp roots, proxy admin URLs, secret values, or original corpus paths.
