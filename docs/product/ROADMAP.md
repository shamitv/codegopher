# CodeGopher Product Roadmap

This roadmap separates the first buildable release from the larger product direction. Dates are intentionally omitted until implementation velocity is known.

## v0.1 - Headless Agent Loop

Goal: `cgopher -p "prompt"` works end-to-end against an OpenAI-compatible provider that supports streaming and tool calls.

Release criteria:

- Package scaffold builds and exposes `codegopher` and `cgopher` entry points.
- Configuration loads from defaults, user/project TOML, environment variables, and CLI flags.
- OpenAI-compatible provider supports streaming text and tool-call events.
- Provider capability checks fail clearly when tool calls are unavailable.
- Core loop executes read/search/list/edit/shell tools through approval-aware orchestration.
- Prior-read enforcement protects edits to existing files.
- Headless mode works in TTY and non-TTY contexts.
- Unit tests cover config loading, provider parsing, tools, approval policy, prior-read tracking, and the mock agent loop.

## v0.2 - Interactive Terminal Experience

Goal: launch `cgopher` into a usable interactive terminal session.

Planned capabilities:

- Textual app shell with chat history, input, status, and tool-call rendering.
- Inline approval prompts for risky actions.
- Slash commands such as `/help`, `/clear`, `/model`, `/mode`, and `/stats`.
- File mention expansion with `@path` and `@glob`.
- Shell passthrough with explicit approval.
- Session save and resume.
- Thinking-content rendering: models that emit chain-of-thought in a `reasoning_content` field (e.g. Qwen3, o-series) should have their thinking displayed distinctly from the final response — collapsed by default in the TUI, dimmed or prefixed in headless `--debug` output, and excluded from `--json` final text.

## v0.3 - Context, Memory, And Skills

Goal: make repeated project work smoother without sacrificing transparency.

Planned capabilities:

- Context-window tracking and compaction.
- Session memory and project-scoped persistent memory.
- Explicit `save_memory` tool.
- Markdown skill discovery from project, user, and built-in locations.
- `.codegopherignore` support across traversal and search tools.
- TODO state for multi-step work.

## v0.4 - Providers And MCP

Goal: expand beyond the first provider while keeping provider behavior explicit.

Planned capabilities:

- Anthropic provider.
- Gemini provider using the maintained `google-genai` SDK.
- Provider capability flags for streaming, tool calls, token counting, thinking controls, and JSON/schema support.
- MCP client integration with managed server lifecycle.
- MCP implementation shape based on the official Python SDK: `StdioServerParameters`, `stdio_client`, `ClientSession(read, write)`, `initialize()`, `list_tools()`, and managed shutdown.
- MCP-derived tools registered dynamically after successful server initialization.

## v0.5 - Repository Documentation And Static Security Skill Packs

Goal: ship built-in Markdown skill packs that help agents document existing repositories and run static-only CRUD application security reviews.

Planned capabilities:

- Built-in `repo-domain-docs` skill for extracting business/functional domain docs from source, tests, and product artifacts.
- Built-in `repo-tech-docs` skill for extracting architecture, setup, API, data-flow, testing, and operations docs.
- Built-in `crud-owasp-static-audit` skill for source-only review against OWASP Top 10:2025.
- `cgopher init --skill-pack repo-docs|security|all` to materialize built-in skills into project `.codegopher/skills`.
- Static-only security boundary: no live probing, fuzzing, credential attacks, dynamic scanners, exploit payloads, or network tests.

## v0.6 - VS Code Extension Layer

Goal: bring CodeGopher into VS Code through a native chat participant while keeping the Python CLI authoritative for tools, approvals, provider behavior, and filesystem safety.

Planned capabilities:

- Native VS Code Chat participant exposed as `@codegopher`.
- JSONL CLI event protocol through `cgopher --events` for IDE and future integrations.
- Streaming assistant text, tool-call progress, tool results, and errors into VS Code Chat.
- Approval buttons in VS Code that route decisions back to the Python agent.
- Extension settings for CLI path, model/provider overrides, approval mode, and protocol tracing.
- Subprocess lifecycle management, cancellation, restart, and clear user-facing errors.

## v0.7 - Advanced Coding Workflows

Goal: support larger changes and safer multi-step execution.

Planned capabilities:

- Planning mode with read-only analysis before execution.
- Sub-agent dispatch for bounded parallel tasks.
- Git diff and worktree helpers.
- Optional Docker-based sandboxing.
- More complete web fetch/search tooling.
- Documentation, examples, and release automation for PyPI.
