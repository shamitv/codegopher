# Session Architecture

CodeGopher uses `AgentSession` as the reusable runtime boundary for multi-turn work.

## Runtime Ownership

- `AgentSession` owns provider-ready conversation state in a `Conversation`.
- `run_agent` remains a compatibility wrapper that creates a fresh `AgentSession` for one headless turn.
- TUI turns reuse one `AgentSession`, so provider calls include prior user, assistant, tool-call, and tool-result messages.
- A session owns a `ToolContext`, including prior-read and inspected-directory grants for the current process only.

## TUI Resume

- TUI session JSON stores display messages separately from `provider_messages`.
- Resume initializes `AgentSession` from persisted provider-ready messages.
- Legacy v0.2 sessions without `provider_messages` load with an empty provider conversation.
- Resume does not restore file-access grants; tools must read or inspect again before editing or creating files.

## Safety Boundaries

- Provider-ready history may be persisted, but API keys, raw environment values, and access-tracker grants must not be serialized.
- Slash commands such as `/clear`, `/stats`, and `/compact` are visible UI actions; normal slash-command text is not added as user provider context.
- `save_memory` is approval-gated and runs through the same tool loop as filesystem and shell tools.
- Headless `cgopher -p` stays one-shot unless a caller explicitly constructs and reuses `AgentSession`.
