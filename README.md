# CodeGopher

> A Python-native, provider-agnostic AI coding agent for your terminal.

CodeGopher v0.2 includes both the original headless command and an interactive Textual TUI for iterative project work. It can stream through an OpenAI-compatible model provider, execute approved tools, expand file mentions, run approved shell commands, and resume local terminal sessions.

## Usage

```bash
cgopher
cgopher -p "What does this project do?"
cgopher -p "read this test log and summarize it" < test.log
cgopher init
```

Run plain `cgopher` in an interactive terminal to open the TUI. Use `-p/--prompt` for the headless one-shot path.
Run `cgopher init [PATH]` to create default project-local Markdown skill guidance under `.codegopher/skills`.

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
- `/model [NAME]`: show or update the active model.
- `/mode [review|auto|yolo]`: show or update approval mode.
- `/stats`: show session counters.
- `/shell COMMAND`: run a shell command after approval unless `yolo` is active.

Prompt helpers:

- `@path`, glob-style mentions such as `@src/**/*.py`, and `@glob:pattern` expand readable text files into the submitted prompt.
- Mention expansion respects project boundaries and `.codegopherignore`.
- Models that emit `reasoning_content` show thinking separately from final answer text; TUI reasoning is collapsed by default.

## Implemented Features

- Headless Click CLI via `codegopher`, `cgopher`, and `python -m codegopher`.
- Interactive Textual TUI for repeated terminal sessions.
- Pydantic settings with CLI, environment, project, user, and default precedence.
- OpenAI-compatible streaming provider with streamed tool-call and reasoning parsing.
- Approval-aware file and shell tools with prior-read and parent-inspection gates.
- Slash commands, file mentions, shell passthrough, and local session save/resume.
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

- Memory, skills, MCP, additional providers, sub-agents, and sandboxing remain future roadmap items.
- Provider capability checks will expand as more model APIs are added.
- Context-window tracking and compaction are planned for larger project sessions.

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

## License

Apache-2.0
