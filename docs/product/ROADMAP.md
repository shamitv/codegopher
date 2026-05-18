# CodeGopher Product Roadmap

This roadmap separates completed release slices from planned work. Dates are intentionally omitted until implementation velocity is known.

## Status Snapshot

| Slice | Status | Notes |
|---|---|---|
| v0.1 - Headless Agent Loop | Done | Implemented and verified. |
| v0.2 - Interactive Terminal Experience | Done | Implemented and verified. |
| v0.3 - Context, Memory, And Skills | Done | Implemented; TODO checklist is complete. |
| v0.4 - OpenAI Responses API And MCP | Done locally | Implemented and locally verified with focused tests; final release checks and manual MCP verification still required. |
| v0.5 - Repository Documentation And Static Security Skill Packs | Done locally | Implemented and locally verified; CI/release review still required. |
| v0.6 - VS Code Extension Layer | TODO | Planned; implementation has not started. |
| v0.7 - Advanced Coding Workflows | TODO | Planned future slice. |

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

TODO:

- Complete full release checks.
- Record manual Playwright MCP and SSE endpoint verification results or blockers.

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

## v0.7 - Advanced Coding Workflows

Status: TODO.

Goal: support larger changes and safer multi-step execution.

TODO:

- Planning mode with read-only analysis before execution.
- Sub-agent dispatch for bounded parallel tasks.
- Git diff and worktree helpers.
- Optional Docker-based sandboxing.
- More complete web fetch/search tooling.
- Documentation, examples, and release automation for PyPI.
