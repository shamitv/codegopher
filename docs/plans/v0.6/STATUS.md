# CodeGopher v0.6 Implementation Status

Last reviewed: 2026-05-18

## Readiness Summary

- v0.6 is planned but not implemented.
- The release goal is a native VS Code Chat extension layer driven by a local `cgopher --events` JSONL protocol.
- Planning now includes VS Code UI for viewing the configured LLM endpoint and managing configured MCP servers.
- No `extensions/vscode` package exists yet.
- No JSONL event protocol exists yet.
- Existing terminal and TUI workflows remain the baseline and must stay compatible.
- v0.4 Responses API and MCP support are implemented and locally verified.
- v0.5 repository documentation and static security skill packs are implemented and locally verified.

Practical readiness estimate:

- Planning docs are present and refreshed for the expanded v0.6 scope.
- Implementation work has not started.
- The first implementation step should define and test protocol models, including redacted config inspection and MCP server management messages, before adding VS Code UI code.

## Current Repository State

| Area | Status | Notes |
|---|---|---|
| v0.1 baseline | Complete | Headless CLI, provider layer, tools, approvals, and tests exist. |
| v0.2 TUI | Complete | Textual TUI, approvals, slash commands, file mentions, shell passthrough, session persistence, and reasoning rendering exist. |
| v0.3 context, memory, and skills | Complete | Context tracking, compaction, memory, Markdown skills, `.codegopherignore`, and session TODOs exist. |
| v0.4 Responses API and MCP | Done locally | OpenAI Responses API, MCP stdio/SSE config, MCP lifecycle, and dynamic approval-gated MCP tools are implemented and locally verified. |
| v0.5 skill packs | Done locally | Repository documentation skills, static OWASP skill, skill-pack init, and implicit project init are implemented and locally verified. |
| v0.6 plan | Present | `PLAN.md` defines the VS Code extension direction plus configured LLM endpoint and MCP server management UI. |
| v0.6 TODO | Present | `TODO.md` breaks work into commit-oriented tasks, with Python config/protocol work before VS Code UI work. |
| JSONL protocol | Not started | Needs typed Python models and CLI routing. |
| Config inspection protocol | Not started | Needs redacted effective `[model]` and selected provider-entry reporting. |
| MCP server management protocol | Not started | Runtime MCP exists, but VS Code-facing list/add/edit/enable/disable/remove flows are not implemented. |
| Events session runner | Not started | Existing `AgentSession` exists; v0.6 still needs an events-oriented wrapper and CLI presentation layer. |
| VS Code scaffold | Not started | No TypeScript package or extension manifest exists. |
| Chat participant | Not started | `@codegopher` is planned but not registered. |
| Approval bridge | Not started | Bidirectional approval over JSONL needs protocol and extension state. |
| Cancellation | Not started | Needs Python turn cancellation and VS Code token handling. |

## Verified Facts

- `docs/product/ROADMAP.md` marks v0.4 OpenAI Responses API And MCP as done locally.
- `docs/product/ROADMAP.md` marks v0.5 Repository Documentation And Static Security Skill Packs as done locally.
- `docs/product/ROADMAP.md` keeps v0.6 as the VS Code Extension Layer and moves Advanced Coding Workflows to v0.7.
- Existing CLI options include `-p/--prompt`, `--model`, `--provider`, `--base-url`, `--api-family`, `--approval-mode`, `--debug`, and `--json`.
- Existing settings include `[model]`, `[[providers.PROVIDER]]`, `[mcp]`, and `[mcp.servers.NAME]`.
- Existing MCP support handles stdio and SSE transports, discovers tools as `mcp__SERVER__TOOL`, and marks MCP tools approval-required.
- Existing approval modes are `review`, `auto`, and `yolo`.
- Existing core callbacks include text deltas, reasoning deltas, tool calls, tool results, approval requests, errors, and completion.
- Existing TUI owns an interactive `ToolContext` for a session.
- Existing session persistence is TUI-specific and should not be treated as the VS Code protocol.
- v0.6 planning now includes `CodeGopher: View LLM Endpoint` and `CodeGopher: Manage MCP Servers`.

## Immediate Blockers

- The protocol schema needs to cover chat events, approval flow, cancellation, redacted config inspection, and MCP server management before extension work can safely begin.
- The config inspection and MCP server management flow needs Python-side validation and redaction so TypeScript does not become authoritative for CodeGopher settings.
- The subprocess approval handshake needs careful design so Python remains authoritative while VS Code owns the user prompt.
- The events session runner needs to support multiple turns without breaking the existing one-shot CLI path.

## Implementation Recommendation

Start with protocol models and Python-side redacted config inspection/MCP server management. Then add Python `--events -p` one-shot streaming, long-lived subprocess mode, and only then scaffold the VS Code extension and its endpoint/MCP command UI.
