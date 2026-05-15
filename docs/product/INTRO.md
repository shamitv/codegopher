# CodeGopher Product Intro

CodeGopher is a Python-native AI coding agent for the terminal. It is designed for developers who want a local, scriptable assistant that can inspect projects, run focused tools, explain code, and make approved changes without requiring a hosted workspace or background server.

The product goal is simple: keep the agent close to the developer's shell, make every risky action visible, and support multiple model providers through a clean provider layer.

## Who It Is For

- Developers who prefer terminal workflows over browser-first coding tools.
- Teams that want a Python package they can install, audit, and extend.
- Users of OpenAI-compatible local or hosted models who want a lightweight coding-agent loop.
- Future users who want richer workflows such as Textual TUI sessions, MCP tools, memory, skills, and sub-agents.

## Core Workflows

- Headless prompt mode: run `cgopher -p "explain this project"` from a shell or script.
- Project inspection: list directories, read files, search text, and summarize findings.
- Approved edits: require prior reads and explicit approval before modifying existing files.
- Shell-assisted debugging: run approved commands with timeouts and clear output capture.
- Provider flexibility: start with OpenAI-compatible streaming chat completions and expand to Anthropic and Gemini later.

## Product Principles

- Terminal-first: the CLI should be useful before the richer TUI exists.
- Provider-aware: adapters should declare capabilities instead of assuming every endpoint behaves the same.
- Safety by default: writes, shell commands, network calls, git operations, and MCP calls are approval-gated unless the user chooses `yolo`.
- Plain files: project config, memory, and skills should live in inspectable local files.
- No server required: CodeGopher should run as a local client process.

## Feature Status

CodeGopher is in early alpha with a working headless v0.1 loop and a narrow set of file and shell tools. Larger product features remain roadmap items:

- Interactive Textual TUI.
- Session and persistent memory.
- Skills loaded from Markdown files.
- MCP client integration.
- Anthropic and Gemini providers, with Gemini based on `google-genai`.
- Sub-agents and git worktree helpers.
- Optional sandboxing.

See the roadmap for sequencing and the initial plan for the v0.1 implementation slice.
