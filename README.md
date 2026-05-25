# CodeGopher

> A Python-native, provider-agnostic AI coding agent for your terminal.

CodeGopher includes both the original headless command and an interactive Textual TUI for iterative project work. It can stream through OpenAI Chat Completions or Responses API, connect configured MCP stdio/SSE servers as approval-gated tools, expand file mentions, manage context, compact long sessions, save memory, load Markdown skills, track session TODOs, and resume local terminal sessions. The current 0.2.1 release also includes repository documentation skills, static security audit skills, chained-vulnerability reporting, and mission contracts that help long-running skill tasks finish with explicit artifacts instead of silent partial results.

## Release Status

Version 0.2.1 is an alpha release. The CLI, TUI, VS Code chat bridge, MCP integration, documentation skills, static security skills, and chained-vulnerability audit path are implemented and locally verified. The development benchmark tooling used to measure audit quality is internal and is not exposed as a public `cgopher` subcommand.

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
cgopher init --skill-pack chained-vulns
cgopher -p "Use @skill:chained-vulnerability-static-audit to review this repository"
```

Run plain `cgopher` in an interactive terminal to open the TUI. Use `-p/--prompt` for the headless one-shot path.
Use `cgopher --events` for the newline-delimited JSON protocol used by IDE integrations, including the VS Code extension.
On first use in a project, CodeGopher creates default local project guidance under `.codegopher/skills/project/SKILL.md`; pass `--no-project-init` to disable that for a run.
Run `cgopher init [PATH]` to create default project-local Markdown skill guidance under `.codegopher/skills`.
Use `cgopher init [PATH] --skill-pack repo-docs|security|chained-vulns|all` to materialize built-in repository documentation and static security review skills into a project.

Useful flags:

- `--model`, `--provider`, and `--base-url` override model/provider settings.
- `--api-family chat_completions|responses` selects the OpenAI-compatible Chat Completions path or OpenAI Responses API path for the run.
- `--approval-mode review|auto|yolo` controls tool approval behavior.
- `--max-iterations N` sets the per-turn agent loop limit; the default is `64`.
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
- Built-in skill packs include `repo-domain-docs`, `repo-tech-docs`, `crud-owasp-static-audit`, and `chained-vulnerability-static-audit`; the security skills are static-only and do not perform live probing, fuzzing, credential attacks, dynamic scanners, exploit payloads, or network tests.
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
To build a local `.vsix` package for VS Code smoke testing, run `npm run package` from `extensions/vscode`; see [the extension README](extensions/vscode/README.md).

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
- Static security report tooling for CRUD OWASP and chained-vulnerability audits, including a dedicated chained report writer.
- Mission contracts and task ledgers for selected complex skills so required TODOs, evidence, tool calls, and report artifacts survive retries and compaction.
- Context-window accounting, manual/automatic compaction, memory, Markdown skills, session TODOs, slash commands, file mentions, shell passthrough, and local session save/resume.
- JSON and JSONL events output for automation, IDE clients, and focused unit/integration test coverage.

## Example Outcomes

These examples were run on sanitized source-only copies of two benchmark-style sample apps. Evaluator files and hint documents were removed before CodeGopher ran, and the detailed reports use only app names and relative file references.

| Task | Sample app | Outcome |
|---|---|---|
| Documentation skills | Banking Transaction Service | Produced architecture, domain, workflow, API, data-store, setup/test, and open-question notes with relative source citations after an explicit file-context retry. |
| Source-grounded question | Charity Donation Platform | Correctly traced refund state changes and the missing refund audit log; the evaluator noted one unsupported comment citation in the answer. |
| Chained vulnerability audit | Banking Transaction Service and Charity Donation Platform | Generated chained audit reports for both apps and matched evaluator ground truth for 4/4 chains and 12/12 components after retrying the larger Banking audit with a higher iteration budget. |
| Code change | Charity Donation Platform | Added a refund audit log call in the sanitized copy and verified Python syntax; no focused test was added because the sanitized app copy did not contain a test suite. |

Detailed release example reports are kept in `docs/release/examples/0.2.1/`.

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

- Improve reliability around empty final responses and environment-sensitive verification commands.
- Continue strengthening source evidence quality for chained vulnerability reports.
- Expand provider capability checks, sandboxing, Git/worktree helpers, and richer coding workflows in later releases.

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
replay_reasoning_content = false

[agent]
max_iterations = 64
```

For OpenAI Responses API, set `api_family = "responses"` or pass `--api-family responses`. Responses calls use `store = false`; CodeGopher keeps the required replay metadata locally.

For OpenAI-compatible local endpoints, set `base_url` on the provider entry and export a key through the configured `api_key_env`. If an upstream requires streamed assistant `reasoning_content` to be sent back in later Chat Completions tool-loop requests, set `replay_reasoning_content = true` or pass `--replay-reasoning-content` for that run.

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
