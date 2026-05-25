# CodeGopher v0.10 Plan - Mission Contracts And Skill-Led Task Ledgers

## Background

v0.9 made the chained-vulnerability benchmark harder and showed that CodeGopher is mostly effective, but still fragile around long-running mission completion. The Qwen all-50 run found 93/100 chains and 253/268 components, yet two apps produced no report and several partials missed required evidence or drifted around decoys. The common failure shape was not simply "model did not know security"; it was "the agent lost or failed to enforce what done means."

CodeGopher already has session TODOs, memory, skill loading, and context compaction. v0.10 connects those pieces into a runtime-owned mission contract so complex tasks retain their goal, required steps, artifacts, and completion gates across context pressure, retries, and provider quirks.

## Goals

- Add a general mission-contract and task-ledger system for complex agent work.
- Let built-in skills declare checklist items, required artifacts, and completion gates through runtime profiles.
- Keep active task state in session/task ledgers, not long-term memory.
- Preserve normal skill usage and public CLI behavior.
- Use chained vulnerability audit as the first strict completion profile.
- Improve documentation and security skills so they explicitly use contract-backed coverage TODOs and completion self-checks.

## Runtime Strategy

- Create core `MissionContract` and `TaskLedger` models that track goal, seeded TODOs, required tool calls, required artifacts, evidence requirements, recovery prompt, recovery attempts, gate failures, and final outcome.
- Resolve a contract profile after skill loading. Skill-specific profiles take precedence over a generic complex-task profile.
- Seed stable TODOs from the active contract without duplicating prior seeded items.
- Inject active contract and open ledger state into provider context and compaction prompts.
- Track observed tool calls and tool results during each turn.
- Validate required tool-call and artifact gates before final completion.
- If gates fail and recovery attempts remain, append a corrective continuation prompt and keep the same turn going.
- If recovery is exhausted, return an explicit incomplete-task result instead of silent success.

## Skill Strategy

- `repo-tech-docs` should use a documentation contract requiring repository inventory, architecture/data-flow notes, setup/runtime notes, API/interface notes, test/ops notes, and explicit unreviewed areas.
- `repo-domain-docs` should use a domain-docs contract requiring capability inventory, actors/workflows, domain model glossary, rules/invariants, evidence notes, and open questions.
- `crud-owasp-static-audit` should use a static-security contract requiring attack-surface inventory, OWASP category coverage, source evidence, missing-test notes, and no-findings reporting when appropriate.
- `chained-vulnerability-static-audit` should use a strict chained-audit contract requiring source-hop-sink evidence, decoy rejection, report writer use, final report artifact, and self-check.
- Security contracts must preserve static-only safety boundaries.

## Events And Persistence

- Persist active and closed task ledgers in TUI session files with a schema version bump.
- Keep headless/events ledgers in process and emit task lifecycle events.
- Add event types for task contract start, update, gate failure, and completion.
- Show active mission status in the TUI through callbacks and status messages.

## Verification Strategy

- Add focused unit tests for profile activation, TODO seeding, context injection, gate validation, recovery prompts, and compaction.
- Add integration-style agent tests for missing report recovery and malformed tool-call JSON recovery.
- Add events protocol tests for task lifecycle events.
- Add TUI session persistence tests for task ledgers.
- Update built-in skill tests for contract-aware guidance.
- Run full Python tests, Ruff, and mypy.
- Re-run focused chained-audit samples for prior v0.9 misses after implementation.

## Out Of Scope

- Public benchmark or mission-contract CLI commands.
- Automatic long-term memory writes for task details.
- Dynamic security testing.
- Full structured report schemas for every skill; v0.10 creates the runtime contract layer first.
