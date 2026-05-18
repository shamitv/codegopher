# CodeGopher v0.4 Placeholder Plan

This placeholder preserves the roadmap slot for Providers And MCP. It is intentionally not expanded into implementation milestones in this branch because the current work is focused on v0.5 built-in skill packs.

## Summary

The v0.4 release should expand CodeGopher beyond the initial OpenAI-compatible provider while keeping provider behavior explicit and testable.

Planned direction:

- Anthropic provider.
- Gemini provider using the maintained `google-genai` SDK.
- Provider capability flags for streaming, tool calls, token counting, thinking controls, and JSON/schema support.
- MCP client integration with managed server lifecycle.
- MCP-derived tools registered dynamically after successful server initialization.

## User-Facing Interfaces

Existing CLI and TUI behavior should remain compatible:

- `cgopher`
- `cgopher -p/--prompt TEXT`
- `--model`, `--provider`, `--base-url`, `--approval-mode`, `--debug`, and `--json`

Expected additions are provider configuration entries and MCP server configuration, but the exact schema should be decided when v0.4 implementation begins.

## Safety And Scope

- Python remains authoritative for provider calls, tool registration, approvals, and filesystem safety.
- MCP tools must be approval-aware and visible to the user before execution.
- Provider adapters must declare capabilities instead of assuming all APIs support the same features.

Out of scope for this placeholder:

- Implementing providers.
- Implementing MCP runtime code.
- Changing the v0.5 skill-pack plan.

## Testing Plan

When v0.4 implementation begins, add tests for provider adapters, capability selection, MCP server lifecycle, dynamic tool registration, approval behavior, and compatibility with existing headless and TUI paths.
