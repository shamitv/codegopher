# v0.17 Focused GPT-5.4-Mini Validation

- Date: 2026-05-31
- Scope: sanitized source-only copies of `app-05`, `app-10`, and `app-14`.
- Model: `gpt-5.4-mini`
- API family: Responses API
- Proxy/model validation: diagnostics route simulation confirmed the requested model routed to the OpenAI provider with upstream model `gpt-5.4-mini`.
- Storage policy: raw event logs, generated app reports, proxy snapshots, temp workspaces, local endpoint values, API key names/values, usernames, and original corpus paths remain outside committed docs. This report contains sanitized aggregate conclusions only.

## Summary

The focused run completed successfully. The benchmark created one proxy stats run, the run was ended, all three app reports were generated through `write_chained_vulnerability_report`, and all three JSON candidate ledgers were valid.

GPT-5.4-mini found `5/8` complete chains and `15/19` required components. The strongest result was `app-14`, where it found all three chains and all required components after one corrective pass. The main misses were chain-bridging gaps in `app-05` and `app-10`, especially around auth/session and state-changing paths.

## Aggregate Stats

| Metric | Result |
|---|---:|
| Apps scanned | 3 |
| Complete chains | 5/8 |
| Components | 15/19 |
| Reports generated | 3/3 |
| Report writer called | 3/3 |
| Valid JSON ledgers | 3/3 |
| Exact evidence items | 81/81 |
| Line references | 53 |
| Attempts | 4 |
| Corrective passes | 1 |
| Ledger repair passes | 0 |
| Candidate-flow repair passes | 0 |
| Provider recovery attempts | 0 |
| Tool-call parse errors | 0 |
| Safety-clean apps | 3/3 |
| Hygiene-passed apps | 3/3 |
| Proxy requests | 26 |
| Proxy errors | 0 |
| Input tokens | 406,186 |
| Output tokens | 19,429 |
| Total tokens | 425,615 |
| Proxy-reported cost | $0.3544 |
| Proxy LLM wall time | 3m 8s |
| Proxy run duration | 3m 10s |

## Per-App Results

| App | Components | Complete Chains | Ledger | Exact Evidence | Line Refs | Attempts | Corrective | Focus Coverage | Candidate Flow |
|---|---:|---:|---|---:|---:|---:|---|---:|---:|
| app-05 | 5/7 | 1/3 | valid | 28/28 | 20 | 1 | no | 76/125 | 20/48 |
| app-10 | 4/6 | 1/2 | valid | 22/22 | 25 | 1 | no | 95/96 | 11/21 |
| app-14 | 6/6 | 3/3 | valid | 31/31 | 8 | 2 | yes | 75/94 | 11/37 |

## What Worked

- Static-only isolation held: no live probing, shell execution, MCP calls, parent traversal, removed-doc access, original-root access, or arbitrary writes were observed.
- Report generation was reliable: every app called `write_chained_vulnerability_report`, produced a final report, and passed JSON candidate-ledger validation.
- Evidence quality was strong: all `81` evidence items were exact, and every completed app had repository-relative paths, symbols, and line or line-range evidence.
- Proxy routing was clean: all `26` proxy requests were model-labeled `gpt-5.4-mini`, used the Responses endpoint, and returned successful status.
- The app-14 corrective pass worked: the initial report had a format/evidence-marker gate issue, and the second attempt produced a valid complete-chain result.

## What Did Not Work

- Recall was still partial overall: app-05 missed two complete chains, and app-10 missed one complete chain.
- Auth/session bridging remained weak: the auth/session family was `0/1` complete and `1/3` components across the focused set.
- Candidate-flow coverage stayed incomplete on app-05 and app-14, with gaps around state-changing and webhook/outbound families.
- The run did not exercise ledger repair or candidate-flow repair, so this does not validate those repair paths for GPT-5.4-mini.
- The agent did not call the explicit `update_todo` tool or save persistent memory in this run; continuity came from mission/task contract updates, provider context, and task-local evidence state.

## Caveat

This was a development-only benchmark run against sanitized source workspaces. It is useful for analyst-assisted evaluation of the chained-audit workflow, but it is not unattended security signoff.
