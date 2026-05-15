# CodeGopher Product Intro

CodeGopher is a Python-native AI coding agent for the terminal. It is designed for developers who want a local assistant that can inspect projects, run focused tools, explain code, and make approved changes without requiring a hosted workspace or background server.

The product goal is simple: keep the agent close to the developer's shell, make every risky action visible, and support multiple model providers through a clean provider layer. CodeGopher now supports both headless one-shot prompts and an interactive Textual TUI session.

## Who It Is For

- Developers who prefer terminal workflows over browser-first coding tools.
- Teams that want a Python package they can install, audit, and extend.
- Users of OpenAI-compatible local or hosted models who want a lightweight coding-agent loop.
- Users who want richer terminal workflows with interactive Textual TUI sessions, local session resume, file mentions, and explicit tool approvals.

## Core Workflows

- Headless prompt mode: run `cgopher -p "explain this project"` from a shell or script.
- Interactive terminal mode: run `cgopher` to open a Textual TUI with chat history, status, inline approvals, slash commands, session resume, and collapsed reasoning display.
- Project inspection: list directories, read files, search text, and summarize findings.
- File mention expansion: include `@path`, glob-style mentions, or `@glob:pattern` in a TUI prompt to provide file content safely.
- Approved edits: require prior reads and explicit approval before modifying existing files.
- Shell-assisted debugging: run approved commands through tools or `/shell COMMAND` with timeouts and clear output capture.
- Provider flexibility: start with OpenAI-compatible streaming chat completions and expand to Anthropic and Gemini later.

## Product Principles

- Terminal-first: both the headless CLI and interactive TUI should feel natural from a shell.
- Provider-aware: adapters should declare capabilities instead of assuming every endpoint behaves the same.
- Safety by default: writes, shell commands, network calls, git operations, and MCP calls are approval-gated unless the user chooses `yolo`.
- Plain files: project config, memory, and skills should live in inspectable local files.
- No server required: CodeGopher should run as a local client process.

## Feature Status

CodeGopher is in early alpha with a working headless loop, an interactive v0.2 TUI, file and shell tools, session persistence, and provider reasoning rendering. Larger product features remain roadmap items:

- Persistent semantic memory beyond local TUI session history.
- Skills loaded from Markdown files.
- MCP client integration.
- Anthropic and Gemini providers, with Gemini based on `google-genai`.
- Sub-agents and git worktree helpers.
- Optional sandboxing.

See the roadmap for sequencing and the initial plan for the v0.1 implementation slice.
