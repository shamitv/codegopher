# Session Architecture

CodeGopher uses `AgentSession` as the reusable runtime boundary for multi-turn work.

## Runtime Ownership

- `AgentSession` owns provider-ready conversation state in a `Conversation`.
- `run_agent` remains a compatibility wrapper that creates a fresh `AgentSession` for one headless turn.
- TUI turns reuse one `AgentSession`, so provider calls include prior user, assistant, tool-call, and tool-result messages.
- A session owns a `ToolContext`, including prior-read grants, inspected-directory grants, memory store access, session TODO state, and task-local episode state for the current process only.
- Episode state records compact observations from tool results and final decisions. It is used for context continuity and compaction, not persistence.

## TUI Resume

- TUI session JSON stores display messages separately from `provider_messages`.
- TUI session JSON also stores loaded skill ids and session TODO items.
- TUI session JSON stores task ledgers, but not task-local episode state.
- Resume initializes `AgentSession` from persisted provider-ready messages.
- Legacy v0.2 sessions without `provider_messages` load with an empty provider conversation.
- Resume does not restore file-access grants; tools must read or inspect again before editing or creating files.
- Resume does not restore episode memory; current-process observations begin fresh.

## Safety Boundaries

- Provider-ready history may be persisted, but API keys, raw environment values, and access-tracker grants must not be serialized.
- Slash commands such as `/clear`, `/stats`, `/compact`, `/memory`, `/skills`, and `/todo` are visible UI actions; normal slash-command text is not added as user provider context.
- `save_memory` is approval-gated and runs through the same tool loop as filesystem and shell tools.
- `update_todo` mutates only session TODO state and is persisted through the TUI session file. It can add, update, start, block, unblock, complete, or cancel TODOs, and the runtime keeps one in-progress item by default.
- Episode memory is not written to memory files or TUI session files.
- Headless `cgopher -p` stays one-shot unless a caller explicitly constructs and reuses `AgentSession`.
