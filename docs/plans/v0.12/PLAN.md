# CodeGopher v0.12 Plan - Evidence-Led Task Memory

## Background

The v0.11 model comparison showed that valid reports and broad discovery are not enough for reliable chained-audit work. Stronger models could find complete chains, but some runs still produced invalid ledgers, hidden-metadata searches, or shallow no-chain conclusions after inspecting relevant files. Smaller and Gemma-class models often kept valid report shape while losing the source-hop-sink synthesis.

v0.12 improves the general runtime instead of tuning to app-01. CodeGopher now keeps task-local episode memory, richer TODO state, stricter mission gates, safer static-audit tool boundaries, and provider telemetry compatibility. The goal is to preserve evidence and unresolved pivots across long tasks without writing audit progress to persistent user memory.

## Goals

- Add ephemeral episode memory for active sessions.
- Improve TODO state so complex tasks can track blocked, cancelled, updated, and evidence-linked items.
- Preserve episode, TODO, memory, skill, and mission context through compaction.
- Strengthen chained-audit mission gates around Candidate Chain Ledger validity, exact evidence, and negative evidence.
- Harden static-audit tools against hidden evaluator metadata, dotfiles, parent traversal, and answer-key searches.
- Add Chat Completions streaming usage compatibility for proxy-observed token and cost stats.
- Prevent proxy benchmark stat contamination from concurrent active runs.
- Update architecture docs for the implemented memory, context, session, skill, provider, and benchmark behavior.

## Runtime Strategy

Episode memory is task-local runtime state. It records compact observations such as source files read, searches performed, TODO updates, report writes, tool errors, and final decisions. It is injected into provider context separately from persistent memories and is preserved during compaction. It is not saved to project or session memory unless a user explicitly asks through the normal approval-gated memory tool.

TODO state now carries richer metadata: status, reason, related files, and evidence references. `update_todo` supports add, update, start, block, unblock, done, and cancel actions. The runtime enforces a single active in-progress item by default so long tasks have one clear current focus.

Mission contracts seed structured TODOs with mission reasons and artifact references. The chained-audit contract requires the report artifact and report writer call as before, but also validates the final report shape before marking the mission complete.

## Chained-Audit Strategy

The chained-audit skill now requires a working candidate ledger before final report writing. No-chain conclusions must include rejected or incomplete candidates with negative evidence. Generic pivot recipes guide source-to-sink synthesis without naming a specific validation app.

Static-audit tool policy now wraps read/search tools and denies hidden evaluator metadata, dotfile and hidden paths, parent traversal, and answer-key terminology searches during chained-audit turns. This moves the safety boundary from prompt-only guidance to a runtime tool constraint.

## Provider And Benchmark Strategy

The OpenAI-compatible Chat Completions provider sends `stream_options: {"include_usage": true}` for streaming calls and retries without it when a compatible route rejects the option. Usage-only stream chunks are ignored by the runtime but remain visible to upstream proxies that collect token and cost stats.

The internal benchmark proxy helper now refuses to start a new run when any active run exists. This avoids request, token, and cost attribution contamination across concurrent model scans.

## Verification Strategy

- Unit tests for episode memory capture, redaction, context injection, and compaction preservation.
- Unit tests for richer TODO status transitions and model-facing tool actions.
- Mission/report tests for Candidate Chain Ledger validity, evidence shape, and no-chain negative evidence.
- Static-audit policy tests for hidden metadata paths, answer-key searches, and parent traversal.
- Provider tests for streaming usage options, fallback retry, and usage-only chunks.
- Benchmark proxy tests for active-run contamination prevention.
- Documentation redaction and architecture consistency checks.

## Success Criteria

- Long-running tasks keep useful source and decision state without writing it to persistent memory.
- Full-recall audit runs must produce valid ledgers, not just correct findings.
- Missed-chain runs must preserve candidate and negative-evidence state instead of shallow no-chain conclusions.
- Static-audit runs cannot access hidden metadata or evaluator-only files through exposed audit tools.
- GPT 5.4-family proxy runs can report token and cost stats when the route supports streamed usage.
- Architecture docs match implemented runtime behavior.
