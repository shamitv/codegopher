# CodeGopher v0.4 TODO

This checklist tracks the v0.4 implementation slice for OpenAI Responses API And MCP. Keep tasks small enough to commit independently.

## Milestone 1 - Planning And Interface Lock

- [x] T001: Replace placeholder v0.4 plan with a decision-complete Responses API and MCP implementation plan.
  Verify: `rg -n "Responses API|Chat Completions|MCP|api_family" docs/plans/v0.4/PLAN.md`
- [x] T002: Replace placeholder v0.4 TODO with granular implementation tasks.
  Verify: `rg -n "Milestone 2|Milestone 3|Playwright MCP" docs/plans/v0.4/TODO.md`
- [x] T003: Update v0.4 status to show refined planning but no runtime implementation yet.
  Verify: `rg -n "Planning refined|Implementation has not started" docs/plans/v0.4/STATUS.md`

## Milestone 2 - Provider Configuration

- [x] T004: Add `ProviderEntry.api_family` with allowed values `chat_completions` and `responses`, defaulting to `chat_completions`.
  Verify: `python -m pytest tests/unit/test_config_schema.py tests/unit/test_config_loader.py`
- [x] T005: Add `CODEGOPHER_API_FAMILY` environment override and `--api-family chat_completions|responses` CLI override.
  Verify: `python -m pytest tests/unit/test_config_loader.py tests/unit/test_cli.py`
- [x] T006: Extend `ProviderCapabilities` with `api_family`, `reasoning_controls`, and `json_schema` fields while preserving existing provider tests.
  Verify: `python -m pytest tests/unit/test_provider_base.py tests/unit/test_provider_registry.py`
- [x] T007: Update runtime provider selection so `api_family = "chat_completions"` selects the current provider and `api_family = "responses"` selects the new Responses provider.
  Verify: `python -m pytest tests/unit/test_provider_registry.py tests/unit/test_cli.py`

## Milestone 3 - Responses API Provider

- [x] T008: Add an OpenAI Responses provider module using `AsyncOpenAI.responses.create(..., stream=True, store=False)`.
  Verify: `python -m pytest tests/unit/test_openai_responses_provider.py`
- [x] T009: Convert CodeGopher messages into stateless Responses `input` items, including previous function calls and function call outputs.
  Verify: `python -m pytest tests/unit/test_openai_responses_provider.py -k input`
- [x] T010: Convert CodeGopher tool schemas into Responses function tool schemas.
  Verify: `python -m pytest tests/unit/test_openai_responses_provider.py -k tool_schema`
- [x] T011: Parse Responses streaming text events into CodeGopher `text_delta` events.
  Verify: `python -m pytest tests/unit/test_openai_responses_provider.py -k text_delta`
- [x] T012: Parse provider-supplied reasoning summary/text events into CodeGopher `reasoning_delta` events without exposing hidden chain-of-thought.
  Verify: `python -m pytest tests/unit/test_openai_responses_provider.py -k reasoning`
- [x] T013: Buffer Responses function call argument events and emit CodeGopher `tool_call` events after valid JSON arguments are complete.
  Verify: `python -m pytest tests/unit/test_openai_responses_provider.py -k tool_call`
- [x] T014: Normalize Responses API request failures, stream failures, failed responses, and malformed function arguments into CodeGopher error events.
  Verify: `python -m pytest tests/unit/test_openai_responses_provider.py -k error`
- [x] T015: Add headless integration coverage proving the Responses provider works with text, tool calls, `--json`, and `--debug`.
  Verify: `python -m pytest tests/integration/test_headless_cli.py tests/integration/test_responses_provider_context.py`

## Milestone 4 - MCP Configuration And Lifecycle

- [x] T016: Add typed `[mcp]` and `[mcp.servers.NAME]` config schema with `enabled`, `transport`, stdio fields, and SSE fields.
  Verify: `python -m pytest tests/unit/test_config_schema.py tests/unit/test_config_loader.py -k mcp`
- [x] T017: Add MCP SSE config support for `url`, `headers`, `headers_env`, `timeout_seconds`, and `sse_read_timeout_seconds`.
  Verify: `python -m pytest tests/unit/test_config_schema.py tests/unit/test_config_loader.py -k "mcp and sse"`
- [x] T018: Ensure MCP SSE header values from `headers` and `headers_env` are not written to settings, sessions, debug output, or errors.
  Verify: `python -m pytest tests/unit/test_cli.py tests/unit/test_tui_session.py -k mcp`
- [x] T019: Add the official Python MCP SDK dependency and keep package build metadata valid.
  Verify: `python -m hatch build`
- [x] T020: Add an MCP transport factory for stdio and SSE using `stdio_client` and `sse_client`.
  Verify: `python -m pytest tests/unit/test_mcp_manager.py`
- [x] T021: Add an MCP manager that opens stdio/SSE transports, calls `initialize()`, lists tools, and shuts sessions down cleanly.
  Verify: `python -m pytest tests/unit/test_mcp_manager.py`
- [x] T022: Add focused stdio lifecycle tests for command startup, tool listing, initialization failure, and cleanup.
  Verify: `python -m pytest tests/unit/test_mcp_manager.py -k stdio`
- [x] T023: Add focused SSE lifecycle tests for URL connection, headers, header env lookup, HTTP timeout, SSE read timeout, initialization failure, and cleanup.
  Verify: `python -m pytest tests/unit/test_mcp_manager.py -k sse`
- [x] T024: Fail fast with a clear configuration error when an enabled MCP server cannot start, connect, or initialize.
  Verify: `python -m pytest tests/unit/test_mcp_manager.py -k failure`
- [x] T025: Ensure MCP sessions are cleaned up after headless runs and TUI session exits.
  Verify: `python -m pytest tests/unit/test_cli.py tests/unit/test_tui_session.py -k mcp`

## Milestone 5 - Dynamic Tools And Approval Flow

- [x] T026: Add an async runtime registry factory that combines built-in tools with MCP-derived tools when MCP is enabled.
  Verify: `python -m pytest tests/unit/test_tools_registry.py tests/unit/test_mcp_tools.py`
- [x] T027: Convert MCP tools into CodeGopher tools named `mcp__SERVER__TOOL` with MCP input schemas preserved as parameters.
  Verify: `python -m pytest tests/unit/test_mcp_tools.py`
- [x] T028: Mark all MCP-derived tools as approval-required and route execution through the existing approval policy.
  Verify: `python -m pytest tests/unit/test_agent_session.py -k mcp`
- [x] T029: Return MCP tool results as CodeGopher `ToolResult.content`, serializing structured MCP content deterministically.
  Verify: `python -m pytest tests/unit/test_mcp_tools.py -k result`
- [x] T030: Add duplicate-name protection for MCP tools by relying on the `mcp__SERVER__TOOL` naming convention.
  Verify: `python -m pytest tests/unit/test_mcp_tools.py -k name`

## Milestone 6 - CLI, TUI, And Docs

- [x] T031: Wire Responses API and MCP startup into headless `cgopher -p` without changing existing output shape.
  Verify: `python -m pytest tests/unit/test_cli.py tests/integration/test_headless_cli.py`
- [x] T032: Wire MCP startup and cleanup into interactive `cgopher` before `launch_tui`.
  Verify: `python -m pytest tests/unit/test_cli.py tests/unit/test_tui_session.py -k mcp`
- [x] T033: Update README and architecture docs with `api_family`, Responses API, MCP stdio config, MCP SSE config, and Playwright MCP examples.
  Verify: `rg -n "api_family|Responses API|mcp.servers|transport = \"sse\"|Playwright MCP" README.md docs/arch docs/product`
- [x] T034: Update v0.4 status after each implementation milestone with completed work and remaining risk.
  Verify: `rg -n "Milestone|Responses API provider|MCP client" docs/plans/v0.4/STATUS.md`

## Milestone 7 - MCP Transport Verification

- [x] T035: Add optional integration verification for an MCP SSE fixture server or a locally controlled SSE endpoint.
  Verify: manual or optional test result recorded in `docs/plans/v0.4/STATUS.md`
- [x] T036: Verify CodeGopher can connect to an MCP SSE endpoint, list tools, execute an approval-gated tool call, and close the SSE session cleanly.
  Verify: manual or optional test result recorded in `docs/plans/v0.4/STATUS.md`
- [x] T037: Add a local/manual verification task for the official Playwright MCP server using `npx @playwright/mcp@latest --headless --isolated`.
  Verify: `rg -n "npx @playwright/mcp@latest --headless --isolated" docs/plans/v0.4`
- [x] T038: Verify CodeGopher can start Playwright MCP over stdio, list browser tools, expose them as `mcp__playwright__*` tools, and shut the server down cleanly.
  Verify: manual check recorded in `docs/plans/v0.4/STATUS.md`
- [x] T039: Verify an approval-gated Playwright MCP browser action against a deterministic test page.
  Verify: manual check recorded in `docs/plans/v0.4/STATUS.md`
- [x] T040: If Node.js, browser installation, network, display constraints, or SSE endpoint availability blocks MCP transport verification, record the blocker and skipped scope explicitly.
  Verify: `rg -n "Playwright MCP|SSE|blocked|skipped" docs/plans/v0.4/STATUS.md`

## Milestone 8 - Release Readiness

- [ ] T041: Run the focused v0.4 unit and integration suite.
  Verify: `python -m pytest tests/unit/test_openai_responses_provider.py tests/unit/test_mcp_manager.py tests/unit/test_mcp_tools.py tests/integration/test_responses_provider_context.py`
- [ ] T042: Run full tests.
  Verify: `python -m pytest`
- [ ] T043: Run lint.
  Verify: `ruff check src/ tests/`
- [ ] T044: Run typecheck.
  Verify: `mypy src/`
- [ ] T045: Build package artifacts.
  Verify: `python -m hatch build`
- [ ] T046: Update roadmap and release checklist for v0.4 completion state.
  Verify: `rg -n "v0.4|Responses API|MCP" docs/product/ROADMAP.md docs/release/CHECKLIST.md`
