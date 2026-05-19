# CodeGopher

> A Python-native, provider-agnostic AI coding agent for your terminal.

CodeGopher includes both the original headless command and an interactive Textual TUI for iterative project work. It can stream through OpenAI Chat Completions or Responses API, connect configured MCP stdio/SSE servers as approval-gated tools, expand file mentions, manage context, compact long sessions, save memory, load Markdown skills, track session TODOs, and resume local terminal sessions.

## Usage

```bash
cgopher
cgopher -p "What does this project do?"
cgopher --no-project-init -p "What does this project do?"
cgopher -p "read this test log and summarize it" < test.log
cgopher --events -p "What does this project do?"
cgopher init
cgopher init --skill-pack repo-docs
cgopher init --skill-pack security
```

Run plain `cgopher` in an interactive terminal to open the TUI. Use `-p/--prompt` for the headless one-shot path.
Use `cgopher --events` for the newline-delimited JSON protocol used by IDE integrations, including the VS Code extension.
On first use in a project, CodeGopher creates default local project guidance under `.codegopher/skills/project/SKILL.md`; pass `--no-project-init` to disable that for a run.
Run `cgopher init [PATH]` to create default project-local Markdown skill guidance under `.codegopher/skills`.
Use `cgopher init [PATH] --skill-pack repo-docs|security|all` to materialize built-in repository documentation and static security review skills into a project.

Useful flags:

- `--model`, `--provider`, and `--base-url` override model/provider settings.
- `--api-family chat_completions|responses` selects the OpenAI-compatible Chat Completions path or OpenAI Responses API path for the run.
- `--approval-mode review|auto|yolo` controls tool approval behavior.
- `--no-project-init` disables first-use project guidance creation for the current run.
- `--json` emits machine-readable headless results.
- `--debug` shows provider reasoning content in headless text output when available.
- `--events` emits JSONL protocol events for IDE and automation clients.

## Interactive TUI

The Textual TUI keeps chat history, streams assistant answers, renders tool calls/results, and shows inline approval prompts. Local session history is saved under CodeGopher's user data directory and automatically resumes for the same project directory.

Slash commands:

- `/help`: show commands.
- `/clear`: clear visible chat history without deleting saved session data.
- `/compact [instructions]`: summarize older provider context while preserving recent turns.
- `/forget ID --yes`: delete a saved memory after confirmation.
- `/memory`: list session and project memories.
- `/model [NAME]`: show or update the active model.
- `/mode [review|auto|yolo]`: show or update approval mode.
- `/stats`: show session counters.
- `/shell COMMAND`: run a shell command after approval unless `yolo` is active.
- `/skills [load ID]`: list or explicitly load Markdown skills.
- `/todo`, `/todo add TEXT`, `/todo done ID`: manage session TODO state.

Prompt helpers:

- `@path`, glob-style mentions such as `@src/**/*.py`, and `@glob:pattern` expand readable text files into the submitted prompt.
- `@skill:ID` explicitly loads a discovered Markdown skill into provider context.
- Mention expansion respects project boundaries and `.codegopherignore`.
- Models that emit `reasoning_content` show thinking separately from final answer text; TUI reasoning is collapsed by default.

Context, memory, skills, and TODOs:

- `/stats` reports context token usage when a provider `context_window` is configured.
- Automatic compaction runs before a turn would exceed the configured threshold; manual `/compact` is always visible in chat.
- `save_memory` stores approved session or project memories under CodeGopher's user data directory, with secret-like values redacted.
- Project skills live in `.codegopher/skills/*/SKILL.md`, user skills live in `~/.codegopher/skills/*/SKILL.md`, and built-in skills ship with the package.
- Built-in v0.5 skill packs include `repo-domain-docs`, `repo-tech-docs`, and `crud-owasp-static-audit`; the security skill is static-only and does not perform live probing, fuzzing, credential attacks, dynamic scanners, exploit payloads, or network tests.
- Active TODOs are included in provider context and can also be updated by the model through the `update_todo` tool.

MCP tools:

- Configure MCP servers in settings under `[mcp.servers.NAME]`.
- `transport = "stdio"` starts a local MCP server process with `command`, `args`, optional `env`, `cwd`, and `startup_timeout_seconds`.
- `transport = "sse"` connects to an SSE MCP endpoint with `url`, optional `headers`, `headers_env`, `timeout_seconds`, and `sse_read_timeout_seconds`.
- MCP tools are exposed as `mcp__SERVER__TOOL`, always require approval, and are cleaned up after headless runs or TUI exit.
- SSE header values and values resolved from `headers_env` are not printed or persisted.

## VS Code Extension

The v0.6 VS Code extension lives in `extensions/vscode` and exposes CodeGopher through native VS Code Chat as `@codegopher`. The extension launches the local Python CLI with `cgopher --events`, so provider setup, config loading, MCP validation, approvals, tool execution, redaction, and filesystem safety remain owned by Python.

Local setup:

```bash
cd extensions/vscode
npm install
npm run compile
npm run lint
npm test
```

For manual development, open the extension package in VS Code, press `F5` to launch an Extension Development Host, open a disposable workspace, and use VS Code Chat with `@codegopher`.

Useful VS Code surfaces:

- `@codegopher /help`: show chat commands.
- `@codegopher /status`: show CLI path, workspace root, provider/model overrides, approval mode, and subprocess state.
- `@codegopher /restart`: restart the local `cgopher --events` subprocess.
- `CodeGopher: Open Chat`: focus VS Code Chat with `@codegopher`.
- `CodeGopher: View LLM Endpoint`: display the effective configured provider, model, API family, base URL, and source metadata without secrets.
- `CodeGopher: Manage MCP Servers`: list, add, edit, enable, disable, and remove configured stdio/SSE MCP servers through Python-side validation.
- `CodeGopher: Show Protocol Trace`: open redacted protocol trace output when `codegopher.traceProtocol` is enabled.

If `cgopher` is not on the VS Code process `PATH`, set `codegopher.cliPath` to the absolute CLI executable path. See [VS Code Extension Testing](docs/devguide/vscode/TESTING.md) for Stable vs Insiders, Windows/macOS/Linux, headless Linux, and manual smoke-test guidance.

## Implemented Features

- Headless Click CLI via `codegopher`, `cgopher`, and `python -m codegopher`.
- Interactive Textual TUI for repeated terminal sessions.
- VS Code extension package with `@codegopher` Chat integration over `cgopher --events`.
- Pydantic settings with CLI, environment, project, user, and default precedence.
- OpenAI-compatible Chat Completions streaming provider with streamed tool-call and reasoning parsing.
- OpenAI Responses API streaming provider with stateless local replay of required response output items.
- MCP stdio/SSE tool discovery and approval-gated execution through the official Python MCP SDK.
- Approval-aware file and shell tools with prior-read and parent-inspection gates.
- Context-window accounting, manual/automatic compaction, memory, Markdown skills, session TODOs, slash commands, file mentions, shell passthrough, and local session save/resume.
- JSON and JSONL events output for automation, IDE clients, and focused unit/integration test coverage.

## Development

Install the package with development tools:

```bash
pip install -e ".[dev]"
```

Useful Hatch scripts:

```bash
hatch run test
hatch run lint
hatch run typecheck
```

## Planned Direction

- Sub-agents, advanced coding workflows, and sandboxing remain future roadmap items.
- Provider capability checks will expand as more provider families are added.
- Git/worktree helpers and richer initialization workflows may expand after the v0.3 release.

## Docs

- [Product Intro](docs/product/INTRO.md)
- [Product Roadmap](docs/product/ROADMAP.md)
- [Initial v0.1 Plan](docs/plans/initial/PLAN.md)
- [llama.cpp OpenAI-Compatible Test Endpoint](docs/devguide/llm/LLAMA_CPP_OPENAI_ENDPOINT.md)
- [VS Code Extension Testing](docs/devguide/vscode/TESTING.md)

## Configuration

CodeGopher uses `~/.codegopher/settings.toml` for user-wide settings and `.codegopher/settings.toml` for per-project settings. CLI flags and environment variables take precedence.

```toml
[model]
provider = "openai"
name = "gpt-4o"

[[providers.openai]]
id = "gpt-4o"
name = "GPT-4o"
api_key_env = "OPENAI_API_KEY"
api_family = "chat_completions"
```

For OpenAI Responses API, set `api_family = "responses"` or pass `--api-family responses`. Responses calls use `store = false`; CodeGopher keeps the required replay metadata locally.

For OpenAI-compatible local endpoints, set `base_url` on the provider entry and export a key through the configured `api_key_env`.

```toml
[mcp.servers.playwright]
enabled = true
transport = "stdio"
command = "npx"
args = ["@playwright/mcp@latest", "--headless", "--isolated"]

[mcp.servers.remote_docs]
enabled = true
transport = "sse"
url = "https://example.test/sse"
headers_env = { Authorization = "MCP_REMOTE_DOCS_AUTHORIZATION" }
timeout_seconds = 5
sse_read_timeout_seconds = 300
```

## License

Apache-2.0
