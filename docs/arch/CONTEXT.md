# Context Architecture

CodeGopher builds provider context from a system prompt, selected runtime context, and the current `Conversation`.

## Context Builder

- `build_messages` prepends a system message to provider-ready conversation messages.
- The system prompt includes cwd, approval mode, available tools, safety rules, and selected memories.
- Slash commands do not enter provider-ready user history unless they intentionally mutate context, such as `/compact`.

## Token Budget

- `context_budget` counts provider messages with `tiktoken`.
- If the configured encoding is unavailable, counting falls back to a deterministic byte estimate.
- The selected provider entry supplies `context_window`.
- Unknown context windows still report token counts but do not warn or compact automatically.
- Default thresholds are warning at 70 percent and compaction at 80 percent of `context_window`.

## Compaction

- Manual compaction is exposed as `/compact [instructions]`.
- Automatic compaction runs before a turn when the pending provider context would exceed the compaction threshold.
- Compaction prompts summarize older user, assistant, tool-call, and tool-result context.
- The most recent user turns stay verbatim in provider-ready history.
- Compaction failure leaves the original conversation unchanged and reports a visible error.
