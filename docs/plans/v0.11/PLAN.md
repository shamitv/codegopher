# CodeGopher v0.11 Plan - Discovery-Gated Chained Audits

## Background

The clean app-01 secure-code-hunt scan showed a sharp failure mode in the chained vulnerability workflow. CodeGopher stayed inside the static-only boundary, called the report writer, produced a valid JSON ledger, cited exact evidence, and avoided removed evaluator files. Even so, it found 0/3 hidden chains and 0/7 hidden chain components.

The failure was not report formatting. It was discovery. The agent spent its limited review budget on health routes, static HTML, JavaScript, and CSS, then repaired ledger quality in the corrective pass. It did not inspect the files that contained the planted attack-chain evidence: controllers, auth/session code, config, validators, upload handlers, TypeScript render sinks, and state-changing endpoints.

v0.11 makes chained audits discovery-gated. A report is not considered substantively complete just because the artifact exists and the ledger is valid. The agent must first cover the source families where chains are likely to live, and corrective passes must close discovery gaps before polishing report shape.

## Goals

- Prioritize discovery before report polish for chained vulnerability audits.
- Improve the source-derived focus queue so high-signal application files outrank repeated static asset matches.
- Add discovery gates that block premature "no complete chains" conclusions when important source families remain unreviewed.
- Make corrective passes read missing high-risk files before repairing ledger structure.
- Update chained-audit skill and mission-contract guidance to require explicit reviewed-file-family coverage.
- Split benchmark analysis into report quality, safety quality, discovery quality, and hidden-chain recall.
- Use app-01 from secure-code-hunt as the main regression case through sanitized scan copies only.

## Non-Goals

- No public `cgopher benchmark` command.
- No dynamic scanning, live probing, fuzzing, credential attacks, exploit scripts, or network tests.
- No app-specific hints, hidden manifest exposure, or benchmark-targeted source path injection into agent-visible prompts.
- No committed raw proxy logs, temp workspaces, generated reports, or benchmark transcripts.
- No replacement of the mission-contract system; v0.11 tightens its chained-audit behavior.

## Discovery Strategy

Focus queue ranking should prefer high-signal application code over repeated low-signal matches. Controllers, routes, auth/session modules, config and secret handling, validators, upload handlers, state-changing services, background jobs, webhook/outbound-call code, repositories, and TS/TSX rendering sinks should appear early and be represented across categories.

Static assets are still relevant when they contain real sources or sinks, such as `innerHTML`, `dangerouslySetInnerHTML`, token handling, API calls, or hardcoded credentials. They should not dominate coverage because of repeated CSS display rules, decorative HTML, or generic shell markup.

The source graph should reward cross-family edges that look like real chains: route to auth check, validator to controller, source-controlled identifier to repository lookup, config secret to session trust, upload parser to mutation sink, webhook URL to outbound fetch, and server data to raw render sink.

## Runtime And Skill Strategy

The chained-audit mission contract should distinguish artifact completion from discovery completion. The report writer and final artifact remain required, but the contract should also require explicit coverage of high-risk source families or an honest incomplete result that says more files must be reviewed.

The `chained-vulnerability-static-audit` skill should instruct the agent to use incomplete findings as pivots. For example, a hardcoded Flask secret should trigger review of session creation, auth routes, role checks, and privileged mutation endpoints before the report can conclude.

When the agent is about to say no complete chains were found, it must first verify that high-risk families were reviewed: route/controller entry points, auth/session, authorization checks, validators, state-changing endpoints, query/expression sinks, external calls, file uploads, background jobs, and rendering sinks.

## Benchmark Strategy

The development benchmark should report four separate dimensions:

- Safety quality: static-only behavior, no parent traversal, no removed-doc access, no unsafe tools.
- Report quality: report artifact, writer call, valid Candidate Chain Ledger, exact evidence, safe-control classification.
- Discovery quality: high-risk source-family coverage, representative file coverage, correction of discovery gaps.
- Hidden-chain recall: full chains and chain components matched against hidden manifests outside the agent-visible workspace.

Corrective prompts should include a compact missing-file-family worklist. The correction should ask the model to read the highest-risk unreviewed files first, then update the report. Format-only repair should come after discovery repair.

## Verification Strategy

- Add deterministic unit tests for focus queue ranking so controllers, auth/session, validators, uploads, jobs, webhooks, query sinks, and TS/TSX render sinks outrank repeated static asset matches.
- Add tests for discovery gates that prevent final "no complete chains" reports when high-risk categories have zero or weak coverage.
- Add tests proving corrective prompts include specific missing source-family worklists instead of only generic quality reminders.
- Add evaluator tests for discovery-quality metrics and their separation from report-quality metrics.
- Re-run app-01 against a sanitized secure-code-hunt copy. The goal is material recall improvement over the clean baseline of 0/3 chains and 0/7 components, not just a valid ledger.

## Success Criteria

- App-01 rerun shows improved discovery of hidden chain files and better recall than the clean baseline.
- Corrective passes spend review budget on missing high-risk source families before ledger polish.
- Reports clearly distinguish "no complete chains after adequate discovery" from "not enough files inspected yet."
- Safety remains clean and static-only boundaries remain enforced.
- Benchmark summaries make it obvious whether a run failed because of safety, report shape, discovery, or actual recall.
