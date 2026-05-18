# CodeGopher v0.4 Implementation Status

Last reviewed: 2026-05-18

## Readiness Summary

- Planning refined: v0.4 now has a concrete implementation plan and granular TODO list for OpenAI Responses API And MCP.
- Implementation has not started in runtime code.
- Existing Chat Completions behavior remains the implemented provider path and the default planned API family.
- Responses API provider support is planned but not implemented.
- MCP client support is planned but not implemented.
- Existing v0.1, v0.2, v0.3, and v0.5 behavior must remain compatible when v0.4 work begins.

## Current Repository State

| Area | Status | Notes |
|---|---|---|
| v0.4 planning docs | Refined | `PLAN.md` and `TODO.md` now describe implementation tasks instead of placeholders. |
| Chat Completions provider | Implemented | Existing OpenAI-compatible provider remains the runtime path. |
| Responses API provider | Not started | No `AsyncOpenAI.responses.create` adapter or stream parser exists yet. |
| API-family config | Not started | No `api_family`, `CODEGOPHER_API_FAMILY`, or `--api-family` support exists yet. |
| MCP config schema | Not started | No typed `[mcp]` settings section exists yet. |
| MCP client lifecycle | Not started | No managed stdio/SSE lifecycle, tool discovery, dynamic MCP tools, or cleanup exists yet. |
| Playwright MCP verification | Not started | Planned as a manual or optional integration verification task. |

## Known Implementation Decisions

- Default provider API family: `chat_completions`.
- New provider API family: `responses`.
- Responses API calls should use `stream=True` and `store=False`.
- Responses API events must be normalized into CodeGopher `StreamEvent` values before reaching the agent loop or TUI.
- MCP transports for v0.4: `stdio` and `sse`.
- MCP Streamable HTTP transport is out of scope for v0.4.
- MCP-derived tools are named `mcp__SERVER__TOOL`.
- MCP-derived tools always require approval and use the existing approval policy.
- Playwright MCP verification should use `npx @playwright/mcp@latest --headless --isolated`.

## Immediate Blockers

- Runtime code still needs config schema changes for provider API-family selection and MCP stdio/SSE servers.
- The official Python MCP SDK dependency has not been added.
- Responses API stream event handling still needs to be implemented and tested against mocked SDK events.
- Dynamic MCP tools need stdio/SSE lifecycle and approval integration before Playwright MCP verification is meaningful.

## Next Recommended Work

Start with Milestone 2 in `TODO.md`: provider configuration. Keep commits small and task-centered, then proceed through Responses provider work before MCP runtime work.
