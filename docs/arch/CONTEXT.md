# Context Architecture

CodeGopher builds provider context from a system prompt, selected runtime context, and the current `Conversation`.

## Context Builder

- `build_messages` prepends a system message to provider-ready conversation messages.
- The system prompt includes cwd, approval mode, available tools, safety rules, selected memories, loaded skills, and active TODO state.
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
- Compaction prompts include selected memories, loaded skills, and active TODOs so summarized history keeps current working state.
- The most recent user turns stay verbatim in provider-ready history.
- Compaction failure leaves the original conversation unchanged and reports a visible error.

## Runtime Context Sources

- Memory context comes from session and project memory selected by `MemoryStore`.
- Skill context comes from Markdown skills loaded by explicit `@skill:ID`, keyword autoload, or `/skills load ID`.
- Built-in skill packs can be materialized into project `.codegopher/skills` with `cgopher init --skill-pack repo-docs|security|all`; once materialized, they use the same context path as any project skill.
- TODO context comes from active session TODO items created through `/todo add` or the `update_todo` tool.
