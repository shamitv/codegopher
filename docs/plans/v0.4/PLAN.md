# CodeGopher v0.4 Placeholder Plan

This placeholder preserves the roadmap slot for OpenAI Responses API And MCP. It is intentionally not expanded into implementation milestones in this branch because the current work is focused on v0.5 built-in skill packs.

## Summary

The v0.4 release should add first-class OpenAI Responses API support and MCP client integration while keeping the current OpenAI-compatible Chat Completions path working.

Planned direction:

- OpenAI Responses API provider path with streaming text and tool-call normalization into CodeGopher's existing provider events.
- Configuration that can select the current OpenAI-compatible Chat Completions path or the new Responses API path without breaking existing projects.
- Provider capability flags for streaming, tool calls, token counting, reasoning controls, and JSON/schema support.
- MCP client integration with managed server lifecycle.
- MCP-derived tools registered dynamically after successful server initialization.

## User-Facing Interfaces

Existing CLI and TUI behavior should remain compatible:

- `cgopher`
- `cgopher -p/--prompt TEXT`
- `--model`, `--provider`, `--base-url`, `--approval-mode`, `--debug`, and `--json`

Expected additions are provider configuration entries for selecting Responses API versus Chat Completions behavior, plus MCP server configuration. The exact schema should be decided when v0.4 implementation begins.

## Safety And Scope

- Python remains authoritative for provider calls, tool registration, approvals, and filesystem safety.
- MCP tools must be approval-aware and visible to the user before execution.
- Provider adapters must declare capabilities instead of assuming all APIs support the same features.
- Responses API events must be normalized into CodeGopher's existing stream event protocol before reaching the agent loop or TUI.

Out of scope for this placeholder:

- Non-OpenAI provider adapters.
- Implementing MCP runtime code.
- Changing the v0.5 skill-pack plan.

## Testing Plan

When v0.4 implementation begins, add tests for Responses API request construction, stream parsing, tool-call normalization, provider capability selection, MCP server lifecycle, dynamic tool registration, approval behavior, and compatibility with existing headless and TUI paths.
