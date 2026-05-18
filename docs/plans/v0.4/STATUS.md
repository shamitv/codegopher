# CodeGopher v0.4 Implementation Status

Last reviewed: 2026-05-18

## Readiness Summary

- v0.4 runtime implementation is complete locally for OpenAI Responses API and MCP stdio/SSE integration.
- Chat Completions remains the default API family and existing config behavior is preserved.
- Responses API support uses `stream=True`, `store=False`, and local replay metadata for required response output items.
- MCP support uses the official Python SDK for stdio and SSE transports, discovers tools as `mcp__SERVER__TOOL`, and marks all MCP tools approval-required.
- Final full-suite checks and manual MCP transport verification still need to be recorded before release.

## Current Repository State

| Area | Status | Notes |
|---|---|---|
| v0.4 planning docs | Done | `PLAN.md` and `TODO.md` describe implementation tasks and verification. |
| API-family config | Done | `ProviderEntry.api_family`, `CODEGOPHER_API_FAMILY`, and `--api-family` are implemented. |
| Chat Completions provider | Done | Existing provider remains the default and strips Responses-only local metadata before requests. |
| Responses API provider | Done | `OpenAIResponsesProvider` streams text, reasoning deltas, function calls, errors, and local metadata replay. |
| MCP config schema | Done | Typed top-level `[mcp]` and stdio/SSE server settings are implemented. |
| MCP client lifecycle | Done | MCP manager opens, initializes, lists tools, registers wrappers, and closes sessions. |
| MCP stdio transport | Done | Uses `StdioServerParameters`, `stdio_client`, and managed `ClientSession`. |
| MCP SSE transport | Done | Uses `sse_client` with configured headers, `headers_env`, and timeouts; missing env vars fail with redacted errors. |
| Dynamic MCP tools | Done | Tools are named `mcp__SERVER__TOOL`, preserve input schemas, require approval, and serialize results deterministically. |
| Headless integration | Done | Headless runtime starts/closes MCP sessions and supports Responses text/tool/debug/JSON flows in tests. |
| TUI integration | Done | TUI starts MCP before agent turns, disables input on MCP init failure, and closes MCP on exit. |
| Playwright MCP verification | Pending | Manual verification planned with `npx @playwright/mcp@latest --headless --isolated`. |
| SSE endpoint verification | Pending | Requires a controlled SSE MCP endpoint or fixture. |

## Verification Recorded

- Focused provider/config/CLI tests passed for the config batch.
- Responses provider and context tests passed:
  - `tests/unit/test_openai_responses_provider.py`
  - `tests/unit/test_openai_compat_provider.py`
  - `tests/unit/test_provider_registry.py`
  - `tests/unit/test_cli.py`
  - `tests/unit/test_agent_session.py`
  - `tests/unit/test_tui_session.py`
  - `tests/integration/test_responses_provider_context.py`
- MCP manager, CLI, and TUI focused tests passed:
  - `tests/unit/test_mcp_client.py`
  - `tests/unit/test_cli.py`
  - `tests/unit/test_tui_agent.py`
- Focused lint and mypy checks passed for the Responses and MCP implementation slices.

## Remaining Release Work

- Run and record final checks:
  - `python -m pytest`
  - `ruff check src/ tests/`
  - `mypy src/`
  - `python -m hatch build`
- Run or explicitly record blockers for:
  - Playwright MCP stdio verification.
  - A controlled MCP SSE endpoint verification.
- Update this status file with final verification results before release tagging.
