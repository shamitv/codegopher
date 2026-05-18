# Providers And MCP

CodeGopher supports two OpenAI API families behind the same provider protocol.

## API Families

- `chat_completions` is the default and uses the existing OpenAI-compatible Chat Completions stream path.
- `responses` uses `AsyncOpenAI.responses.create(..., stream=True, store=False)`.
- `CODEGOPHER_API_FAMILY` and `--api-family chat_completions|responses` override the selected provider entry for one run.
- Responses API history is stateless with local metadata replay: CodeGopher stores required response output items such as function calls and encrypted reasoning items in local conversation state instead of relying on OpenAI-hosted state.

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
