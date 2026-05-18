# CodeGopher v0.4 Implementation Plan

This plan covers the v0.4 implementation slice: first-class OpenAI Responses API support and MCP client integration while preserving the existing OpenAI-compatible Chat Completions path.

## Summary

The current runtime provider path is OpenAI-compatible Chat Completions. v0.4 adds a second OpenAI API family, Responses API, and adds MCP servers as dynamically discovered, approval-aware tools.

Goals:

- Keep existing Chat Completions behavior as the default and avoid breaking existing `.codegopher/settings.toml` files.
- Add a Responses API provider path that normalizes typed Responses streaming events into CodeGopher's existing `StreamEvent` protocol.
- Add MCP stdio and SSE client support with managed connection lifecycle, tool discovery, dynamic tool registration, approval-gated execution, and clean shutdown.
- Keep Python authoritative for provider calls, MCP tool execution, approvals, filesystem safety, and TUI/headless behavior.

Out of scope:

- Non-OpenAI provider adapters.
- Streamable HTTP MCP transport.
- OpenAI built-in hosted tools such as web search, file search, and computer use.
- Changes to v0.5 skill packs or v0.6 VS Code extension work.

## Public Interfaces

Provider selection:

- Add `ProviderEntry.api_family` with allowed values `chat_completions` and `responses`.
- Default `api_family` to `chat_completions` so existing configs keep working.
- Add `--api-family chat_completions|responses` and `CODEGOPHER_API_FAMILY` as one-run overrides for the selected provider entry.
- Keep `--provider openai`, `--model`, `--base-url`, `api_key_env`, `temperature`, and `max_output_tokens` behavior compatible.

Provider capabilities:

- Extend `ProviderCapabilities` with `api_family`, `reasoning_controls`, and `json_schema` fields.
- Register the existing provider implementation as the OpenAI Chat Completions path.
- Add a new OpenAI Responses provider path selected when the chosen provider entry has `api_family = "responses"`.

MCP configuration:

- Add a top-level `[mcp]` settings section with `enabled = true` by default.
- Add server entries under `[mcp.servers.NAME]` with `enabled`, `transport`, and transport-specific fields.
- Support `transport = "stdio"` with `command`, `args`, `env`, `cwd`, and `startup_timeout_seconds`.
- Support `transport = "sse"` with `url`, `headers`, `headers_env`, `timeout_seconds`, and `sse_read_timeout_seconds`.
- Do not print or persist SSE header values, especially values loaded from `headers_env`.
- Example Playwright MCP stdio config:

```toml
[mcp.servers.playwright]
enabled = true
transport = "stdio"
command = "npx"
args = ["@playwright/mcp@latest", "--headless", "--isolated"]
startup_timeout_seconds = 30
```

Example MCP SSE config:

```toml
[mcp.servers.remote_docs]
enabled = true
transport = "sse"
url = "https://example.test/sse"
headers_env = { Authorization = "MCP_REMOTE_DOCS_AUTHORIZATION" }
timeout_seconds = 5
sse_read_timeout_seconds = 300
```

## Implementation Details

Responses API provider:

- Add a provider module that uses `AsyncOpenAI.responses.create(..., stream=True, store=False)`.
- Send CodeGopher conversation history as stateless Responses `input` items.
- Convert system, user, and assistant text messages to Responses message input items.
- Convert previous assistant tool calls to Responses `function_call` items and tool results to `function_call_output` items using the existing CodeGopher tool call IDs.
- Convert CodeGopher tool schemas from Chat Completions shape into Responses function tool shape.
- Map `response.output_text.delta` to `text_delta`.
- Map provider-supplied reasoning summary/text deltas, when present, to `reasoning_delta`; do not synthesize or expose hidden chain-of-thought.
- Buffer streamed function call argument deltas and emit CodeGopher `tool_call` events only after arguments are complete and valid JSON.
- Map provider `error`, failed response, malformed tool arguments, and SDK exceptions to CodeGopher `error` events followed by `done`.
- Emit `done` on `response.completed` or after the stream closes cleanly.

MCP runtime:

- Add an MCP manager that opens configured stdio and SSE transports with the official Python MCP SDK, calls `initialize()`, lists tools, and owns cleanup.
- For stdio servers, spawn the configured command with `StdioServerParameters` and `stdio_client`.
- For SSE servers, connect to the configured URL with `sse_client` and apply configured headers, header environment lookups, HTTP timeout, and SSE read timeout.
- Convert each MCP tool to a CodeGopher `Tool` with name `mcp__SERVER__TOOL`.
- Preserve the MCP tool input schema as the CodeGopher tool parameters schema.
- Mark all MCP-backed tools as `requires_approval = True`.
- Execute MCP tools through the existing approval path and return textual or JSON-serialized MCP results as `ToolResult.content`.
- If a configured MCP server fails to start or connect, fail fast with a clear `ConfigurationError` naming the server and transport.
- Shut down all started MCP sessions after a headless run and when the TUI session exits.

Compatibility:

- Existing headless `cgopher -p`, TUI `cgopher`, `--json`, `--debug`, implicit project init, skills, memory, TODO state, and approval modes must continue to work.
- If MCP is disabled or no servers are configured, the runtime should behave exactly like the current static tool registry.
- Chat Completions tests remain valid and should not be rewritten around Responses API concepts.

## Testing And Verification

Unit coverage:

- Config schema, env, and CLI override tests for `api_family` and MCP server config.
- Provider registry/runtime tests proving Chat Completions remains default and Responses is selected only when configured.
- Responses provider tests for request construction, message/input conversion, tool schema conversion, text deltas, reasoning deltas, function call argument buffering, malformed arguments, failed responses, and SDK errors.
- MCP manager tests with fake stdio, SSE, and session implementations for server initialization, tool listing, schema conversion, duplicate-safe tool naming, execution, errors, and cleanup.
- Agent/session tests proving dynamically registered MCP tools flow through the existing approval mechanism.

Integration and smoke coverage:

- Headless tests for Chat Completions compatibility.
- Headless tests for Responses API provider context, tool calls, `--json`, and `--debug` reasoning display.
- TUI launch/session tests proving MCP startup happens before the session and cleanup happens on exit.
- Manual or optional integration verification using Playwright MCP with `npx @playwright/mcp@latest --headless --isolated`.

Final checks:

- `python -m pytest`
- `ruff check src/ tests/`
- `mypy src/`
- `python -m hatch build`
