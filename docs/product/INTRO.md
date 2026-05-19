# CodeGopher Product Intro

CodeGopher is a Python-native AI coding agent for the terminal and VS Code. It is designed for developers who want a local assistant that can inspect projects, run focused tools, explain code, and make approved changes without requiring a hosted workspace or background server.

The product goal is simple: keep the agent close to the developer's workspace, make every risky action visible, and support multiple model providers through a clean provider layer. CodeGopher now supports headless one-shot prompts, an interactive Textual TUI session, a VS Code IDE workflow through `@codegopher`, Responses API selection, MCP tool integration, and context features for repeated project work.

## Who It Is For

- Developers who prefer terminal workflows over browser-first coding tools.
- Developers who want an IDE-native VS Code Chat entry point without moving provider calls, tools, approvals, or config semantics out of the local Python engine.
- Teams that want a Python package they can install, audit, and extend.
- Users of OpenAI-compatible local or hosted models who want a lightweight coding-agent loop.
- Users who want richer terminal workflows with interactive Textual TUI sessions, local session resume, file mentions, memory, skills, TODO tracking, compaction, and explicit tool approvals.

## Core Workflows

- Headless prompt mode: run `cgopher -p "explain this project"` from a shell or script.
- Interactive terminal mode: run `cgopher` to open a Textual TUI with chat history, status, inline approvals, slash commands, session resume, and collapsed reasoning display.
- VS Code IDE mode: use `@codegopher` in VS Code Chat for streaming answers, tool progress, approval buttons, cancellation, restart, endpoint inspection, and MCP server management through the same local Python agent.
- Context management: inspect context budget through `/stats` and summarize long provider history through `/compact [instructions]`.
- Memory: save approved session or project memory, inspect it with `/memory`, and remove it with `/forget ID --yes`.
- Skills: initialize project skill guidance with `cgopher init`, materialize built-in skill packs with `cgopher init --skill-pack repo-docs|security|all`, load Markdown skills from `.codegopher/skills`, and mention them with `@skill:ID`.
- Session TODOs: track active work with `/todo`, `/todo add TEXT`, `/todo done ID`, or the model-facing `update_todo` tool.
- Project inspection: list directories, read files, search text, and summarize findings.
- File mention expansion: include `@path`, glob-style mentions, or `@glob:pattern` in a TUI prompt to provide file content safely.
- Approved edits: require prior reads and explicit approval before modifying existing files.
- Shell-assisted debugging: run approved commands through tools or `/shell COMMAND` with timeouts and clear output capture.
- Provider flexibility: use OpenAI-compatible streaming chat completions by default, opt into OpenAI Responses API, and attach stdio/SSE MCP servers as approval-gated tools.

## Product Principles

- Terminal-first: both the headless CLI and interactive TUI should feel natural from a shell.
- Provider-aware: adapters should declare capabilities instead of assuming every endpoint behaves the same.
- Safety by default: writes, shell commands, network calls, git operations, and MCP calls are approval-gated unless the user chooses `yolo`.
- Plain files: project config, memory, and skills should live in inspectable local files.
- No server required: CodeGopher should run as a local client process.

## Feature Status

CodeGopher is in early alpha with a working headless loop, an interactive TUI, a VS Code `@codegopher` chat extension, file and shell tools, session persistence, provider reasoning rendering, Responses API support, MCP stdio/SSE integration, context-window tracking, compaction, memory, Markdown skills, built-in repository documentation and static security skill packs, and session TODO state. Larger product features remain roadmap items:

- Sub-agents and git worktree helpers.
- Optional sandboxing.

See the roadmap for sequencing and the initial plan for the v0.1 implementation slice.
