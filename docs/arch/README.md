# Architecture Docs

These docs describe implemented CodeGopher runtime architecture.

- [SESSION](SESSION.md): reusable `AgentSession`, provider-ready history, task-local episode state, TUI resume, and session safety.
- [CONTEXT](CONTEXT.md): context builder, token budget accounting, thresholds, compaction, skills, persistent memory, episode memory, TODOs, and mission state.
- [MEMORY](MEMORY.md): persistent local memory, task-local episode memory, `save_memory`, TUI memory commands, redaction, and context injection.
- [SKILLS](SKILLS.md): Markdown skill discovery, built-in skill packs, mission contracts, chained-audit report gates, and static-only security boundaries.
- [PROVIDERS_MCP](PROVIDERS_MCP.md): Chat Completions/Responses provider selection, streaming usage compatibility, proxy-safe benchmark runs, and MCP stdio/SSE tool lifecycle.
