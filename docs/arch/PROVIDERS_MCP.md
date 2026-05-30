# Providers And MCP

CodeGopher supports two OpenAI API families behind the same provider protocol.

## API Families

- `chat_completions` is the default and uses the existing OpenAI-compatible Chat Completions stream path.
- `responses` uses `AsyncOpenAI.responses.create(..., stream=True, store=False)`.
- `CODEGOPHER_API_FAMILY` and `--api-family chat_completions|responses` override the selected provider entry for one run.
- `replay_reasoning_content = true`, `CODEGOPHER_REPLAY_REASONING_CONTENT=true`, or `--replay-reasoning-content` enables a Chat Completions compatibility mode for upstreams that require assistant `reasoning_content` to be replayed after tool calls. The default is `false`.
- Responses API history is stateless with local metadata replay: CodeGopher stores required response output items such as function calls and encrypted reasoning items in local conversation state instead of relying on OpenAI-hosted state.
- Chat Completions streaming requests include `stream_options: {"include_usage": true}` by default so compatible proxies can observe token and cost usage on streaming calls.
- If a route rejects `stream_options` or `include_usage`, the provider retries the same request without the option.
- Usage-only stream chunks are ignored by the runtime event stream; provider-visible text, reasoning, tool-call, error, and done events keep the existing shape.

## Development Benchmark Proxy Safety

The internal chained-audit benchmark can start and end proxy admin runs for request, token, and cost accounting. The proxy helper refuses to start a run when any active run already exists, even if it looks CodeGopher-owned, because concurrent active runs contaminate attribution.

Benchmark reports may include sanitized aggregate metrics. Raw proxy snapshots, local endpoint values, temp roots, generated event logs, and API key names must stay out of committed docs.

## MCP Runtime

MCP servers are configured under `[mcp.servers.NAME]`. `transport = "stdio"` uses `StdioServerParameters`, `stdio_client`, and `ClientSession`; `transport = "sse"` uses `sse_client` with configured headers and timeouts.

Startup sequence:

1. Build the default tool registry.
2. Open each enabled MCP server transport.
3. Create a `ClientSession`, call `initialize()`, and list tools.
4. Register each tool as `mcp__SERVER__TOOL`.
5. Close all MCP sessions after headless completion or TUI exit.

All MCP-derived tools require approval. Tool schemas are preserved from MCP input schemas. Text results are returned directly when possible; mixed or structured MCP results are serialized deterministically as JSON.

SSE header values and values resolved from `headers_env` are passed only to the MCP client. They must not be written to settings, session files, debug output, or user-facing errors.
