# CodeGopher

> A Python-native, provider-agnostic AI coding agent for your terminal.

CodeGopher v0.1 is a headless command that can run a prompt, stream through an OpenAI-compatible model provider, execute approved tools, and return a result.

## Target v0.1 Experience

```bash
cgopher -p "What does this project do?"
cgopher -p "read this test log and summarize it" < test.log
```

Use `--json` for machine-readable output, `--approval-mode yolo` for unprompted local execution, and `--base-url` to target an OpenAI-compatible endpoint.

## Implemented v0.1 Features

- Headless Click CLI via `codegopher`, `cgopher`, and `python -m codegopher`.
- Pydantic settings with CLI, environment, project, user, and default precedence.
- OpenAI-compatible streaming provider with streamed tool-call parsing.
- Approval-aware file and shell tools with prior-read and parent-inspection gates.
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

- Headless terminal workflow first.
- OpenAI-compatible provider support for the initial release.
- Approval-gated file and shell tools.
- Prior-read enforcement before editing existing files.
- Later milestones for the interactive Textual TUI, memory, skills, MCP, additional providers, sub-agents, and sandboxing.

## Docs

- [Product Intro](docs/product/INTRO.md)
- [Product Roadmap](docs/product/ROADMAP.md)
- [Initial v0.1 Plan](docs/plans/initial/PLAN.md)
- [llama.cpp OpenAI-Compatible Test Endpoint](docs/devguide/llm/LLAMA_CPP_OPENAI_ENDPOINT.md)

## Configuration Direction

CodeGopher will use `~/.codegopher/settings.toml` for user-wide settings and `.codegopher/settings.toml` for per-project settings. CLI flags and environment variables will take precedence.

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
