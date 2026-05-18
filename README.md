# CodeGopher

> A Python-native, provider-agnostic AI coding agent for your terminal.

CodeGopher v0.3 includes both the original headless command and an interactive Textual TUI for iterative project work. It can stream through an OpenAI-compatible model provider, execute approved tools, expand file mentions, manage context, compact long sessions, save memory, load Markdown skills, track session TODOs, and resume local terminal sessions.

## Usage

```bash
cgopher
cgopher -p "What does this project do?"
cgopher -p "read this test log and summarize it" < test.log
cgopher init
cgopher init --skill-pack repo-docs
cgopher init --skill-pack security
```

Run plain `cgopher` in an interactive terminal to open the TUI. Use `-p/--prompt` for the headless one-shot path.
Run `cgopher init [PATH]` to create default project-local Markdown skill guidance under `.codegopher/skills`.
Use `cgopher init [PATH] --skill-pack repo-docs|security|all` to materialize built-in repository documentation and static security review skills into a project.

Useful flags:

- `--model`, `--provider`, and `--base-url` override model/provider settings.
- `--approval-mode review|auto|yolo` controls tool approval behavior.
- `--json` emits machine-readable headless results.
- `--debug` shows provider reasoning content in headless text output when available.

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

## Implemented Features

- Headless Click CLI via `codegopher`, `cgopher`, and `python -m codegopher`.
- Interactive Textual TUI for repeated terminal sessions.
- Pydantic settings with CLI, environment, project, user, and default precedence.
- OpenAI-compatible streaming provider with streamed tool-call and reasoning parsing.
- Approval-aware file and shell tools with prior-read and parent-inspection gates.
- Context-window accounting, manual/automatic compaction, memory, Markdown skills, session TODOs, slash commands, file mentions, shell passthrough, and local session save/resume.
- JSON output for automation and focused unit/integration test coverage.

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

- MCP, additional providers, sub-agents, advanced coding workflows, and sandboxing remain future roadmap items.
- Provider capability checks will expand as more model APIs are added.
- Git/worktree helpers and richer initialization workflows may expand after the v0.3 release.

## Docs

- [Product Intro](docs/product/INTRO.md)
- [Product Roadmap](docs/product/ROADMAP.md)
- [Initial v0.1 Plan](docs/plans/initial/PLAN.md)
- [llama.cpp OpenAI-Compatible Test Endpoint](docs/devguide/llm/LLAMA_CPP_OPENAI_ENDPOINT.md)

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
```

For OpenAI-compatible local endpoints, set `base_url` on the provider entry and export a key through the configured `api_key_env`.

## License

Apache-2.0
