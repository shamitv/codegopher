## Executive Summary Snapshot

Current eval status is mixed. The chained-audit benchmark harness is good at execution control, static-only safety, report generation, and now exact evidence validation. It is weaker at complete vulnerability discovery on the hardest level-5 apps. Harness2 remains the best observed recall baseline, while harness3 is the current evidence-quality direction.

The current practical read is:

- Best detection run: harness2, with `9/11` full chains and `30/32` components.
- Current evidence-quality run: harness3, with `117/117` exact evidence objects and `7/9` valid ledgers.
- Current limitation: harness3 improved evidence validation but regressed recall to `7/11` full chains and raised cost per completed chain.
- Recommended use: analyst-assisted triage and evidence collection, not unattended security signoff.

## Timeline

| Run | Scope | Full chains | Components | Evidence quality | Requests | Tokens | Cost | Read |
|---|---|---:|---:|---|---:|---:|---:|---|
| `20260526-231207-gpt54nano-complex2-responses` | Two complex apps | `1/4` | `7/12` | Low line-reference coverage; decoy handling weak on Warehouse | 38 | 410,192 | `$0.04541176` | Safe execution, weak detection. |
| `20260527-000753-gpt54nano-complex2-structured` | Same two apps | `2/4` | `10/12` | Line references and candidate ledgers appeared; decoy misfires dropped to zero | 18 | 285,323 | `$0.05061751` | Better structure and component recall, still incomplete. |
| `20260527-003016-gpt54nano-complex2-followup` | Same two apps | `3/4` | `11/12` | More source-reading effort and corrective behavior | 32 | 486,006 | `$0.06689424` | Reached 75% full-chain recall at higher cost. |
| `20260527-005709-gpt54nano-level5-harness2` | Nine level-5 apps | `9/11` | `30/32` | JSON ledgers mostly present, but exact evidence only `21/98` | 159 | 2,243,454 | `$0.33409596` | Best observed detection baseline. |
| `20260527-091723-gpt54nano-level5-harness3` | Same nine level-5 apps | `7/11` | `27/32` | Exact evidence `117/117`; valid ledgers `7/9`; focus coverage `629/967` | 153 primary, 161 full proxy | 2,535,758 primary, 2,703,113 full proxy | `$0.36991300` primary, `$0.38679010` full proxy | Better evidence validator, worse vulnerability finder. |

Harness3's full proxy bucket included eight successful Chat Completions requests routed to a different visible model. The primary benchmark stats are the cleaner cost basis for `gpt-5.4-nano` Responses API evaluation.

## What Worked

- Static isolation held across the expanded runs. The harness used sanitized code-only temp workspaces and did not observe dynamic probing, shell execution, MCP calls, memory writes, parent traversal, removed-doc access, original-corpus access, or arbitrary writes.
- Report completion became reliable. Harness2 and harness3 generated reports for all nine level-5 apps and called the required report writer in every app.
- Structured prompts improved coverage of source-hop-sink reasoning, line-numbered evidence, and candidate-chain ledgers compared with the baseline Responses run.
- Decoy scoring improved. Safe-control mentions stopped being counted as misfires unless they were used as exploit evidence, and recent expanded runs had zero decoy misfires.
- Harness3 made evidence machine-checkable. Every parsed harness3 candidate-ledger evidence object had exact relative path, symbol, and line or line range.
- Focus coverage exposed blind spots that recall alone hid, especially missed route/entrypoint, helper, display, outbound-fetch, and rendering categories.

## What Did Not Work

- Harness3 recall regressed. Full-chain recall fell from harness2's `9/11 = 81.8%` to `7/11 = 63.6%`, and component recall fell from `30/32 = 93.8%` to `27/32 = 84.4%`.
- Prompt and schema weight likely consumed attention budget. Harness3 produced cleaner ledgers, but the model sometimes optimized for evidence format over complete source exploration.
- Focus coverage was measured better than it was used. Harness3 recorded `629/967 = 65.0%` focus-category coverage, below target, but the corrective pass did not reliably recover missed high-signal areas.
- Evidence and conclusion could still diverge. Earlier structured runs showed reports that cited expected components while marking a chain rejected or incomplete.
- Candidate headings remain noisy. Unmatched candidate headings rose in richer ledger outputs, so title normalization still needs work.
- Cost efficiency worsened in harness3. Primary cost per completed full chain was `$0.0528`, compared with harness2's `$0.0371`.

## Cost And Efficiency

Harness2 cost `$0.33409596` for `9` completed full chains, or about `$0.0371` per completed full chain. Harness3 primary benchmark cost `$0.36991300` for `7` completed full chains, or about `$0.0528` per completed full chain. The full harness3 proxy bucket cost was `$0.38679010`, but it included a mixed-model caveat.

Token usage followed the same pattern. Harness3 primary usage was `2,535,758` tokens, up from harness2's `2,243,454`, while completed full chains decreased. The next implementation pass should reduce prompt bulk and use targeted focus worklists instead of adding more generic instructions.

## Vulnerability Coverage

The benchmark currently exercises chained vulnerabilities, not standalone scanner findings. The strongest observed families are:

- IDOR and IDOR/XSS chains: predictable or disclosed identifiers, missing ownership or tenant checks, and raw or staff-visible sinks.
- Injection chains: SQL query construction, LDAP filter construction, expression/query builder pivots, and follow-on privileged mutation or disclosure.
- SSRF and outbound-fetch pivots: URL, callback, webhook, redirect, or label-generation input flowing to internal fetch or auth/session-adjacent sinks.
- Auth/session/token chains: reset, invite, reusable token, predictable reference, or trust-transition flows that can lead to account/session takeover or privilege change.
- Supporting exposure chains: verbose errors, config or actuator exposure, generated references, helper prerequisites, raw display builders, summary/receipt/label renderers, and safe-control decoys.

Harness2 recall by family on the nine-app run was:

| Family | Full chains | Components |
|---|---:|---:|
| auth/session | `1/1` | `3/3` |
| IDOR | `2/3` | `7/8` |
| injection | `3/4` | `11/12` |
| SSRF | `3/3` | `9/9` |

## Current Eval Implementation

The harness runs development-only chained-vulnerability audits through sanitized workspaces. It removes evaluator-facing hints, launches CodeGopher with a static-only chained-audit prompt, captures events, writes generated reports, and evaluates the result against hidden manifests.

Current capabilities include:

- Source-derived focus queue and lightweight source graph prompt context.
- Generic chain-family checklist for auth, IDOR, injection, SSRF, token, helper, rendering, config, race/state, and filesystem/archive style chains.
- Bounded corrective second pass when reports miss structural gates, exact evidence, safe-control classification, or high-signal focus coverage.
- Ground-truth scoring for full-chain recall, component recall, difficulty, family, required evidence, and decoy misuse.
- Report-quality scoring for line references, unmatched candidate headings, JSON candidate-ledger presence/validity, exact evidence objects, safe-control classifications, and focus coverage.
- `read_file(include_line_numbers=true)` support for final code evidence collection.

## Source Material

- Baseline Responses report: `docs/plans/v0.10/report/20260526-231207-gpt54nano-complex2-responses/REPORT.md`
- Structured two-app report: `docs/plans/v0.10/report/20260527-000753-gpt54nano-complex2-structured/REPORT.md`
- Follow-up two-app report: `docs/plans/v0.10/report/20260527-003016-gpt54nano-complex2-followup/REPORT.md`
- Harness2 level-5 report: `docs/plans/v0.10/report/20260527-005709-gpt54nano-level5-harness2/REPORT.md`
- Harness3 level-5 report: `docs/plans/v0.10/report/20260527-091723-gpt54nano-level5-harness3/REPORT.md`
- Harness3 comparison: `docs/plans/v0.10/report/20260527-091723-gpt54nano-level5-harness3/COMPARISON_WITH_PREVIOUS.md`

