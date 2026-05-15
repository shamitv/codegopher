# CodeGopher Initial Implementation Plan

This plan covers the v0.1 implementation slice only: a buildable Python package with a headless agent loop, OpenAI-compatible provider support, approval-aware tools, and focused tests. Broader product work lives in `docs/product/ROADMAP.md`.

## Summary

The v0.1 release should prove the core agent architecture before investing in the interactive TUI, memory, skills, MCP, sub-agents, or extra providers. The target user experience is:

```bash
cgopher -p "explain this project"
cgopher -p "read the failing test output and suggest a fix" < test.log
```

For v0.1, agentic execution requires a provider endpoint that supports streaming chat completions and tool calls. Endpoints without tool-call support must fail with a clear configuration error instead of silently degrading.

## Package And Entry Points

Create the package using the existing `src/codegopher` layout and Hatch build metadata.

- Distribution name: `codegopher`.
- Import package: `codegopher`.
- CLI commands: `codegopher` and `cgopher`.
- Python support: 3.11+.
- Primary runtime dependencies: `openai`, `click`, `pydantic`, `httpx`, `rich`, `tiktoken`, and standard-library async/file APIs.
- Development dependencies: `pytest`, `pytest-asyncio`, `pytest-mock`, `pytest-httpx`, `ruff`, `mypy`, and `hatch`.

Keep non-v0.1 dependencies out of the critical path unless already needed by package metadata. Gemini work must use `google-genai` when that provider is added.

## Configuration

Implement a typed settings model with Pydantic v2.

```python
class ApprovalMode(str, Enum):
    review = "review"
    auto = "auto"
    yolo = "yolo"

class ModelConfig(BaseModel):
    provider: str = "openai"
    name: str = "gpt-4o"
    temperature: float = 1.0
    max_output_tokens: int = 8192

class ProviderEntry(BaseModel):
    id: str
    name: str
    base_url: str | None = None
    api_key_env: str | None = None
    context_window: int | None = None

class Settings(BaseModel):
    model: ModelConfig = ModelConfig()
    providers: dict[str, list[ProviderEntry]] = {}
    approval_mode: ApprovalMode = ApprovalMode.review
    ignore_file: str = ".codegopherignore"
    debug: bool = False
```

Load settings in this precedence order, highest wins:

1. CLI flags.
2. Environment variables such as `CODEGOPHER_MODEL`, `CODEGOPHER_APPROVAL_MODE`, `OPENAI_API_KEY`, and provider-specific key variables.
3. `.codegopher/settings.toml` in the current project.
4. `~/.codegopher/settings.toml`.
5. Built-in defaults.

Configuration errors should include the setting name, source, and expected value shape.

## Provider Layer

Define a small provider protocol that normalizes model output into internal stream events.

```python
class ProviderCapabilities(BaseModel):
    streaming: bool
    tool_calls: bool
    token_counting: bool

class ToolCall(TypedDict):
    id: str
    name: str
    arguments: dict[str, Any]

class StreamEvent(TypedDict):
    type: Literal["text_delta", "tool_call", "done", "error"]

class Provider(Protocol):
    capabilities: ProviderCapabilities

    async def stream(
        self,
        messages: list[Message],
        tools: list[ToolSchema],
        *,
        model: str,
        temperature: float,
        max_output_tokens: int,
    ) -> AsyncIterator[StreamEvent]: ...
```

Implement `OpenAICompatProvider` first.

- Use `AsyncOpenAI` with configurable `base_url` and API key environment variable.
- Parse streaming text deltas and complete tool calls into internal `StreamEvent` values.
- Require `ProviderCapabilities.tool_calls` for v0.1 agentic execution.
- Add explicit errors for missing API keys, unsupported model capability, malformed tool arguments, and provider stream failures.
- Token counting may use `tiktoken` when available and fall back to a documented approximation.

Do not assume every OpenAI-compatible endpoint behaves identically. The provider registry must select an adapter and check capabilities before the agent loop starts.

## Tool System

Define a common tool interface.

```python
class ToolResult(BaseModel):
    tool_call_id: str
    content: str
    is_error: bool = False

class Tool(Protocol):
    name: str
    description: str
    parameters: dict[str, Any]
    requires_approval: bool

    async def execute(self, arguments: dict[str, Any], context: ToolContext) -> ToolResult: ...
```

Implement these v0.1 tools:

- `read_file`: read a UTF-8 text file with optional line bounds and record the canonical path as read.
- `read_many_files`: read bounded sets of files from explicit paths or globs and record each canonical path as read.
- `list_dir`: list a directory and record the canonical directory path as inspected.
- `glob_search`: return matching paths while respecting `.codegopherignore`.
- `grep_search`: search text using Python or `rg` when available, respecting `.codegopherignore`.
- `write_file`: create or replace files, approval required.
- `edit_file`: apply targeted text edits, approval required.
- `run_shell_command`: run a subprocess with timeout, approval required.

Network fetch, web search, git helpers, MCP tools, memory tools, skills, and sub-agents are out of scope for v0.1.

## Approval Policy

Document and implement the approval decision in one place.

```python
def should_prompt(mode: ApprovalMode, tool: Tool) -> bool:
    return mode == ApprovalMode.auto or (
        mode == ApprovalMode.review and tool.requires_approval
    )
```

Approval modes:

- `review`: prompt for write/edit/delete, shell, git, network, MCP, and other risky tools.
- `auto`: prompt for every tool call, including reads.
- `yolo`: never prompt.

In headless mode:

- If stdin is a TTY, prompt interactively before executing required tools.
- If stdin is not a TTY and mode is not `yolo`, deny tools that require approval and return a tool error to the model.
- If mode is `yolo`, execute without prompting.

## Prior-Read Enforcement

Use a session-scoped tracker for canonical paths.

- Resolve paths relative to the current working directory.
- Normalize to absolute canonical paths.
- On Windows, compare canonical paths case-insensitively.
- `read_file`, `read_many_files`, and explicit `@file` expansion count as file reads.
- `list_dir` counts as parent directory inspection for new-file creation.
- `edit_file` and replacement writes to existing files require a prior read of the same canonical path in the current session.
- Creating a new file requires approval and a prior inspection of the canonical parent directory.
- Shell commands remain approval-gated because their file effects cannot be reliably inferred.

Rejected writes should return a structured tool error that tells the model which read or directory inspection is required.

## Core Agent Loop

Implement an async loop that is independent of the CLI presentation layer.

1. Build context from system prompt, conversation history, current user prompt, tool schemas, and minimal project metadata.
2. Check provider capabilities before starting the first turn.
3. Stream provider output to callbacks.
4. Collect tool calls until the provider turn ends.
5. If there are no tool calls, append the assistant message and return final text.
6. Execute tool calls sequentially in v0.1 through approval and prior-read gates.
7. Append assistant tool-call messages and tool results to history.
8. Continue until final text or a max-iteration guard is reached.

The system prompt must state the current working directory, available tools, approval mode, and safety rules. It should not mention unimplemented memory, skills, MCP, sub-agents, or TUI features.

## Headless CLI

Implement the Click command in `codegopher.cli.main`.

Target options:

- `-p, --prompt TEXT`: run one headless prompt and exit.
- `--model TEXT`: override model name.
- `--provider TEXT`: override provider group.
- `--base-url TEXT`: override provider endpoint.
- `--approval-mode [review|auto|yolo]`: choose approval behavior.
- `--json`: emit machine-readable final output and tool summaries.
- `--debug`: include debug diagnostics.

Behavior:

- If `--prompt` is present, run headless mode.
- If stdin is piped, append stdin content to the user prompt as input context.
- If no prompt is present, print a short alpha message pointing to the roadmap instead of starting the future TUI.
- Exit nonzero for configuration errors, provider errors, and max-iteration failures.

## Testing Plan

Unit tests:

- Config precedence and validation.
- `ApprovalMode` parsing and `should_prompt` behavior.
- Provider stream parsing with mocked OpenAI-compatible chunks.
- Capability failure when tool calls are unavailable.
- Path canonicalization and prior-read checks on Windows-style and POSIX-style paths.
- File tools using temporary directories.
- Shell tool timeout, success, and failure cases.
- Agent loop with a scripted mock provider.

Integration-style tests:

- Headless CLI with a mock provider.
- Non-TTY approval denial behavior.
- JSON output shape.

Static checks:

- `ruff check src/ tests/`.
- `mypy src/`.
- `pytest`.

## Out Of Scope For v0.1

- Interactive Textual TUI.
- Memory and skills.
- MCP client integration.
- Anthropic and Gemini providers.
- Web search and network fetch tools.
- Sub-agents.
- Git worktree helpers.
- Docker sandboxing.
- Release publishing automation.

These are planned in the product roadmap after the headless vertical slice is stable.
