# CodeGopher Product Roadmap

This roadmap separates completed release slices from planned work. Dates are intentionally omitted until implementation velocity is known.

## Status Snapshot

| Slice | Status | Notes |
|---|---|---|
| v0.1 - Headless Agent Loop | Done | Implemented and verified. |
| v0.2 - Interactive Terminal Experience | Done | Implemented and verified. |
| v0.3 - Context, Memory, And Skills | Done | Implemented; TODO checklist is complete. |
| v0.4 - OpenAI Responses API And MCP | Done locally | Implemented and locally verified with full tests, lint, typecheck, build, Playwright MCP stdio, and controlled MCP SSE checks. |
| v0.5 - Repository Documentation And Static Security Skill Packs | Done locally | Implemented and locally verified; CI/release review still required. |
| v0.6 - VS Code Extension Layer | Done locally | Implemented and locally verified; manual/release review remains tracked in the v0.6 plan. |
| v0.7 - Chained Vulnerability Detection | Done locally | Built-in chained-vulnerability skill, static audit policy, attack graph/report scaffolding, docs, and tests are implemented; CI/release review remains. |
| v0.8 - Richer IDE UI And Webview Work | TODO | Future slice for custom VS Code panels that still rely on the Python engine. |

## v0.1 - Headless Agent Loop

Status: Done.

Goal: `cgopher -p "prompt"` works end-to-end against an OpenAI-compatible provider that supports streaming and tool calls.

Done:

- Package scaffold builds and exposes `codegopher` and `cgopher` entry points.
- Configuration loads from defaults, user/project TOML, environment variables, and CLI flags.
- OpenAI-compatible provider supports streaming text and tool-call events.
- Provider capability checks fail clearly when tool calls are unavailable.
- Core loop executes read/search/list/edit/shell tools through approval-aware orchestration.
- Prior-read enforcement protects edits to existing files.
- Headless mode works in TTY and non-TTY contexts.
- Unit tests cover config loading, provider parsing, tools, approval policy, prior-read tracking, and the mock agent loop.

## v0.2 - Interactive Terminal Experience

Status: Done.

Goal: launch `cgopher` into a usable interactive terminal session.

Done:

- Textual app shell with chat history, input, status, and tool-call rendering.
- Inline approval prompts for risky actions.
- Slash commands including `/help`, `/clear`, `/model`, `/mode`, and `/stats`.
- File mention expansion with `@path`, glob-style mentions, and `@glob:pattern`.
- Shell passthrough with explicit approval.
- Session save and resume.
- Thinking-content rendering: provider `reasoning_content` is distinct from answer text, collapsed by default in the TUI, visible in headless `--debug`, and excluded from `--json` final text.

## v0.3 - Context, Memory, And Skills

Status: Done.

Goal: make repeated project work smoother without sacrificing transparency.

Done:

- Context-window tracking and manual/automatic compaction.
- Session memory and project-scoped persistent memory.
- Approval-gated `save_memory` tool.
- Markdown skill discovery from project, user, and built-in locations.
- `.codegopherignore` support across traversal and search tools.
- Session TODO state for multi-step work, including `/todo` commands and model-facing `update_todo`.
- Default project skill initialization through `cgopher init [PATH]`.

## v0.4 - OpenAI Responses API And MCP

Status: Done locally.

Goal: add first-class OpenAI Responses API support and MCP integration while preserving the existing OpenAI-compatible Chat Completions path.

Done:

- OpenAI Responses API provider path with streaming and tool-call normalization.
- Configuration that can select Responses API versus the existing OpenAI-compatible Chat Completions behavior.
- Provider capability flags for streaming, tool calls, token counting, reasoning controls, and JSON/schema support.
- MCP client integration with managed stdio/SSE server lifecycle.
- MCP implementation based on the official Python SDK: `StdioServerParameters`, `stdio_client`, `sse_client`, `ClientSession(read, write)`, `initialize()`, `list_tools()`, and managed shutdown.
- MCP-derived tools registered dynamically after successful server initialization and marked approval-required.

Verified locally:

- Full tests, lint, typecheck, and package build passed.
- Playwright MCP stdio listed browser tools and executed an approval-gated browser action.
- Controlled MCP SSE verification listed and executed a tool with `headers_env`.

## v0.5 - Repository Documentation And Static Security Skill Packs

Status: Done locally.

Goal: ship built-in Markdown skill packs that help agents document existing repositories and run static-only CRUD application security reviews.

Done:

- Built-in `repo-domain-docs` skill for extracting business/functional domain docs from source, tests, and product artifacts.
- Built-in `repo-tech-docs` skill for extracting architecture, setup, API, data-flow, testing, and operations docs.
- Built-in `crud-owasp-static-audit` skill for source-only review against OWASP Top 10:2025.
- `cgopher init --skill-pack repo-docs|security|all` materializes built-in skills into project `.codegopher/skills`.
- Implicit first-use project initialization creates `.codegopher/skills/project/SKILL.md` when `.codegopher/` is absent.
- `--no-project-init` disables implicit project initialization for a run.
- Static-only security boundary: no live probing, fuzzing, credential attacks, dynamic scanners, exploit payloads, or network tests.
- Local verification passed with full tests, lint, typecheck, build, package-content check, and path guard.

TODO:

- Run CI and release review.

## v0.6 - VS Code Extension Layer

Status: TODO.

Goal: bring CodeGopher into VS Code through a native chat participant while keeping the Python CLI authoritative for tools, approvals, provider behavior, and filesystem safety.

TODO:

- Native VS Code Chat participant exposed as `@codegopher`.
- JSONL CLI event protocol through `cgopher --events` for IDE and future integrations.
- Streaming assistant text, tool-call progress, tool results, and errors into VS Code Chat.
- Approval buttons in VS Code that route decisions back to the Python agent.
- Extension settings for CLI path, model/provider overrides, approval mode, and protocol tracing.
- Subprocess lifecycle management, cancellation, restart, and clear user-facing errors.
- Configured LLM endpoint viewing and MCP server management through VS Code-native controls, not a custom webview.

## v0.7 - Chained Vulnerability Detection

Status: Done locally.

Goal: detect source-to-sink exploit chains where multiple modest weaknesses combine into high-impact security outcomes.

Done locally:

- Built-in `chained-vulnerability-static-audit` Markdown skill for static-only attack-graph review.
- `cgopher init --skill-pack chained-vulns`, with `security` and `all` packs updated to include the chained audit skill.
- TUI `/audit --chain` entry point that submits a normal skill-backed audit prompt.
- Static audit tool policy that restricts chained-audit turns to read/list/search, TODO updates, and the dedicated chained report writer.
- Attack graph models, Mermaid rendering, report writing, scan coordinator scaffolding, and chain linker scaffolding.
- Unit and integration tests for skill materialization, static policy, graph/report generation, coordinator/linker behavior, TUI routing, and VS Code prompt forwarding.

TODO:

- Run CI and release review.

## v0.8 - Richer IDE UI And Webview Work

Status: TODO.

Goal: add richer VS Code UI surfaces after the first chat-based extension is stable, while continuing to keep the Python engine authoritative.

TODO:

- Custom VS Code webview panels for richer chat, MCP server management, endpoint inspection, logs, and visual state where native chat and command-palette flows are too limited.
- Webview-to-extension message bridge that forwards actions to `cgopher --events` instead of reimplementing agent logic in TypeScript.
- Frontend state, accessibility, keyboard navigation, theming, and VS Code webview security hardening.
- Tests for webview message passing, state synchronization, redaction, and subprocess error recovery.
