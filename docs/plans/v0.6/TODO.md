# CodeGopher v0.6 Fine-Grained TODO

This checklist is intentionally commit-oriented. Each checkbox should normally be one focused commit. Keep implementation work small enough that failures can be reverted without losing unrelated progress.

Commit rules:

- Complete, verify, and commit each task before starting the next task.
- Include the task id in the commit message, for example `T006 Add events protocol base models`.
- Preserve existing `cgopher`, `cgopher -p/--prompt`, `--json`, `--debug`, and TUI behavior.
- Keep Python authoritative for config loading, MCP validation, tools, approvals, provider behavior, and filesystem safety.
- Do not execute CodeGopher tools or MCP tools directly from TypeScript.
- Do not parse, validate, or write CodeGopher settings TOML from TypeScript.
- Redact API keys, raw environment values, MCP header values, and values resolved through `headers_env`.
- Prefer protocol and Python config tests before VS Code UI work.
- Before each commit, run the smallest relevant verification command listed for that task.

## Milestone 0 - Planning And Roadmap Setup

- [x] T001: Add the v0.6 roadmap entry for the VS Code extension layer.
  Verify: `rg -n "v0.6|VS Code Extension Layer|@codegopher" docs/product/ROADMAP.md`
- [x] T002: Add `docs/plans/v0.6/PLAN.md` with the implementation plan.
  Verify: `test -f docs/plans/v0.6/PLAN.md`
- [x] T003: Add `docs/plans/v0.6/TODO.md` with commit-oriented milestones.
  Verify: `test -f docs/plans/v0.6/TODO.md`
- [x] T004: Add `docs/plans/v0.6/STATUS.md` with initial status and blockers.
  Verify: `test -f docs/plans/v0.6/STATUS.md`
- [x] T005: Refresh v0.6 planning docs for configured LLM endpoint viewing and MCP server management.
  Verify: `rg -n "View LLM Endpoint|Manage MCP Servers|configured LLM endpoint|MCP server" docs/plans/v0.6`

## Milestone 1 - JSONL Protocol Models

- [x] T006: Add typed protocol models for common event and command fields.
  Verify: `python -m pytest tests/unit/test_events_protocol.py`
- [x] T007: Add command models for `start_turn`, `approval_response`, `cancel_turn`, and `shutdown`.
  Verify: `python -m pytest tests/unit/test_events_protocol.py`
- [x] T008: Add command models for `get_effective_config`, `list_mcp_servers`, `save_mcp_server`, `set_mcp_server_enabled`, and `delete_mcp_server`.
  Verify: `python -m pytest tests/unit/test_events_protocol.py`
- [x] T009: Add event models for session, turn, text, reasoning, tool, approval, error, and completion events.
  Verify: `python -m pytest tests/unit/test_events_protocol.py`
- [x] T010: Add event models for `config_snapshot`, `mcp_servers`, `mcp_server_saved`, and `mcp_server_deleted`.
  Verify: `python -m pytest tests/unit/test_events_protocol.py`
- [x] T011: Add JSONL encode/decode helpers that reject malformed or unknown payloads clearly.
  Verify: `python -m pytest tests/unit/test_events_protocol.py`
- [x] T012: Add protocol redaction tests for secrets, raw environment values, and MCP header values.
  Verify: `python -m pytest tests/unit/test_events_protocol.py`

## Milestone 2 - Config Inspection And MCP Management

- [x] T013: Add a Python effective-config inspector for `[model]` and the selected `[[providers.PROVIDER]]` entry.
  Verify: `python -m pytest tests/unit/test_config_inspection.py`
- [x] T014: Report redacted LLM endpoint details: provider, model, API family, base URL when present, and configuration source metadata.
  Verify: `python -m pytest tests/unit/test_config_inspection.py`
- [x] T015: Add a redacted MCP server listing helper for configured `[mcp.servers.NAME]` entries.
  Verify: `python -m pytest tests/unit/test_config_inspection.py`
- [x] T016: Add a project-local settings update helper for MCP server mutations that preserves unrelated settings.
  Verify: `python -m pytest tests/unit/test_config_management.py`
- [x] T017: Add MCP server add/edit support using the existing stdio/SSE settings schema and validation.
  Verify: `python -m pytest tests/unit/test_config_management.py tests/unit/test_config_schema.py -k mcp`
- [x] T018: Add MCP server enable, disable, and remove support.
  Verify: `python -m pytest tests/unit/test_config_management.py`
- [x] T019: Return structured config errors for invalid server names, invalid transport-specific fields, and invalid TOML.
  Verify: `python -m pytest tests/unit/test_config_management.py`
- [x] T020: Prove config inspection and MCP management never expose secrets and never write user-global settings.
  Verify: `python -m pytest tests/unit/test_config_inspection.py tests/unit/test_config_management.py`

## Milestone 3 - Events Session Runner

- [x] T021: Add an events session wrapper around the existing agent session that owns settings, provider, registry, cwd, MCP manager, and `ToolContext`.
  Verify: `python -m pytest tests/unit/test_events_session.py`
- [x] T022: Keep existing `run_agent` behavior compatible while sharing reusable session code where appropriate.
  Verify: `python -m pytest tests/unit/test_agent_loop.py tests/integration/test_headless_cli.py`
- [x] T023: Add multi-turn events-session tests proving prior-read and directory-inspection state persists within a session.
  Verify: `python -m pytest tests/unit/test_events_session.py tests/unit/test_tool_context.py`
- [x] T024: Add callback-to-protocol event translation for text, reasoning, tools, approvals, errors, and completion.
  Verify: `python -m pytest tests/unit/test_events_session.py tests/unit/test_events_protocol.py`
- [x] T025: Add cancellation hooks for an active events session turn.
  Verify: `python -m pytest tests/unit/test_events_session.py`
- [x] T026: Add structured events-session errors for provider failure, agent-loop failure, cancellation, config failure, and bad approval state.
  Verify: `python -m pytest tests/unit/test_events_session.py`

## Milestone 4 - `cgopher --events` CLI Mode

- [x] T027: Add CLI routing for `--events -p PROMPT` without changing existing `--json` output.
  Verify: `python -m pytest tests/unit/test_cli.py tests/integration/test_headless_cli.py`
- [x] T028: Emit JSONL events for one-shot text responses.
  Verify: `python -m pytest tests/integration/test_events_cli.py`
- [x] T029: Emit JSONL events for reasoning deltas without including reasoning in final text.
  Verify: `python -m pytest tests/integration/test_events_cli.py tests/unit/test_agent_loop.py`
- [x] T030: Emit tool-call and tool-result events for a multi-iteration response.
  Verify: `python -m pytest tests/integration/test_events_cli.py`
- [x] T031: Support approval requests and stdin `approval_response` in one-shot events mode.
  Verify: `python -m pytest tests/integration/test_events_cli.py tests/unit/test_approval.py`
- [x] T032: Add long-lived `cgopher --events` mode that accepts `start_turn` commands over stdin.
  Verify: `python -m pytest tests/integration/test_events_cli.py`
- [x] T033: Accept effective-config and MCP server management commands in long-lived events mode.
  Verify: `python -m pytest tests/integration/test_events_cli.py tests/unit/test_config_management.py`
- [x] T034: Support `cancel_turn` and `shutdown` commands in long-lived events mode.
  Verify: `python -m pytest tests/integration/test_events_cli.py`
- [x] T035: Route human diagnostics to stderr while reserving stdout for protocol JSONL.
  Verify: `python -m pytest tests/integration/test_events_cli.py`
- [x] T036: Preserve existing non-interactive no-prompt error when `--events` is not present.
  Verify: `python -m pytest tests/unit/test_cli.py`

## Milestone 5 - VS Code Extension Scaffold

- [x] T037: Add `extensions/vscode/package.json` with extension metadata, chat commands, endpoint/MCP commands, settings, and scripts.
  Verify: `cd extensions/vscode && npm install`
- [x] T038: Add TypeScript, ESLint, and test configuration for the extension package.
  Verify: `cd extensions/vscode && npm run compile`
- [x] T039: Add a minimal extension activation entry point.
  Verify: `cd extensions/vscode && npm test`
- [x] T040: Add activation tests using the VS Code extension test runner.
  Verify: `cd extensions/vscode && npm test`
- [x] T041: Add extension README notes for local development.
  Verify: `rg -n "CodeGopher|@codegopher|cgopher --events" extensions/vscode`

## Milestone 6 - Subprocess Protocol Client

- [x] T042: Add a TypeScript JSONL parser with partial-line buffering.
  Verify: `cd extensions/vscode && npm test`
- [x] T043: Add a CodeGopher subprocess client that launches `cgopher --events` in the workspace root.
  Verify: `cd extensions/vscode && npm test`
- [x] T044: Add typed event routing for all protocol event types.
  Verify: `cd extensions/vscode && npm test`
- [x] T045: Add pending request tracking for turns and approvals.
  Verify: `cd extensions/vscode && npm test`
- [x] T046: Add subprocess client helpers for effective-config and MCP server management commands.
  Verify: `cd extensions/vscode && npm test`
- [x] T047: Add stderr capture and structured subprocess exit errors.
  Verify: `cd extensions/vscode && npm test`
- [x] T048: Add restart and shutdown lifecycle behavior.
  Verify: `cd extensions/vscode && npm test`
- [x] T049: Add trace logging with redaction when `codegopher.traceProtocol` is enabled.
  Verify: `cd extensions/vscode && npm test`

## Milestone 7 - Chat Participant

- [x] T050: Register the `@codegopher` chat participant in the extension manifest and activation code.
  Verify: `cd extensions/vscode && npm test`
- [x] T051: Stream `text_delta` events into VS Code Chat markdown.
  Verify: `cd extensions/vscode && npm test`
- [x] T052: Render `tool_call` and `tool_result` events as progress and compact chat summaries.
  Verify: `cd extensions/vscode && npm test`
- [x] T053: Render provider and protocol errors as user-facing chat errors.
  Verify: `cd extensions/vscode && npm test`
- [x] T054: Hide reasoning deltas by default while surfacing reasoning progress in trace/debug paths.
  Verify: `cd extensions/vscode && npm test`
- [x] T055: Implement `/help` and `/status` chat commands.
  Verify: `cd extensions/vscode && npm test`
- [x] T056: Implement `/restart` chat command.
  Verify: `cd extensions/vscode && npm test`

## Milestone 8 - Endpoint And MCP Configuration UI

- [x] T057: Implement `CodeGopher: View LLM Endpoint` using the Python `get_effective_config` response.
  Verify: `cd extensions/vscode && npm test`
- [x] T058: Display provider, model, API family, base URL, and config source for the configured LLM endpoint without secrets.
  Verify: `cd extensions/vscode && npm test`
- [x] T059: Implement `CodeGopher: Manage MCP Servers` list view with server name, enabled state, transport, and source.
  Verify: `cd extensions/vscode && npm test`
- [x] T060: Add MCP server creation flows for stdio and SSE servers.
  Verify: `cd extensions/vscode && npm test`
- [x] T061: Add MCP server edit flows for supported non-secret fields.
  Verify: `cd extensions/vscode && npm test`
- [x] T062: Add MCP server enable, disable, and remove flows with confirmation for destructive actions.
  Verify: `cd extensions/vscode && npm test`
- [x] T063: Surface Python validation and config-write errors in VS Code without raw secret values.
  Verify: `cd extensions/vscode && npm test`
- [x] T064: Add VS Code command tests for endpoint display and MCP server management flows.
  Verify: `cd extensions/vscode && npm test`

## Milestone 9 - Approval And Cancellation UX

- [x] T065: Render approval requests with Approve and Deny chat buttons.
  Verify: `cd extensions/vscode && npm test`
- [x] T066: Route Approve button clicks to `approval_response`.
  Verify: `cd extensions/vscode && npm test`
- [x] T067: Route Deny button clicks to `approval_response` with a default denial reason.
  Verify: `cd extensions/vscode && npm test`
- [x] T068: Prevent duplicate approval decisions for the same approval id.
  Verify: `cd extensions/vscode && npm test`
- [x] T069: Respect VS Code cancellation tokens by sending `cancel_turn`.
  Verify: `cd extensions/vscode && npm test`
- [x] T070: Confirm the subprocess can run another turn after cancellation or denial.
  Verify: `cd extensions/vscode && npm test`

## Milestone 10 - Settings, Errors, And Workspace Handling

- [x] T071: Implement `codegopher.cliPath` resolution with clear missing-executable errors.
  Verify: `cd extensions/vscode && npm test`
- [x] T072: Pass configured provider, model, base URL, API family, and approval mode overrides to the CLI.
  Verify: `cd extensions/vscode && npm test`
- [x] T073: Select the workspace root deterministically and show it in `/status`.
  Verify: `cd extensions/vscode && npm test`
- [x] T074: Handle multi-root workspaces with a clear default and user-facing status.
  Verify: `cd extensions/vscode && npm test`
- [x] T075: Add user-facing recovery guidance for subprocess crashes and invalid protocol messages.
  Verify: `cd extensions/vscode && npm test`
- [x] T076: Add output-channel logging for extension lifecycle events.
  Verify: `cd extensions/vscode && npm test`

## Milestone 11 - Docs, Packaging, And Release Readiness

- [x] T077: Update README with VS Code extension usage and setup.
  Verify: `rg -n "VS Code|@codegopher|--events" README.md`
- [x] T078: Update product intro to mention the v0.6 IDE workflow.
  Verify: `rg -n "VS Code|IDE|@codegopher" docs/product/INTRO.md`
- [x] T079: Update release checklist with VS Code extension smoke tests.
  Verify: `rg -n "VS Code|@codegopher|extension" docs/release/CHECKLIST.md`
- [x] T080: Add local VSIX packaging instructions.
  Verify: `rg -n "vsix|package" extensions/vscode README.md docs`
- [x] T081: Write detailed VS Code extension testing guidelines under `docs/devguide`, covering macOS, Windows, and Linux, including Stable vs Insiders usage, Extension Development Host debugging, CLI test caveats, and headless Linux notes.
  Verify: `rg -n "macOS|Windows|Linux|Insiders|Extension Development Host|headless" docs/devguide`
- [x] T082: Run the complete Python test suite.
  Verify: `source .venv/bin/activate && python -m pytest`
- [x] T083: Run Python lint and type checks.
  Verify: `source .venv/bin/activate && ruff check src/ tests/ && mypy src/`
- [x] T084: Run extension compile, lint, and tests.
  Verify: `cd extensions/vscode && npm run compile && npm run lint && npm test`
- [ ] T085: Build Python distribution artifacts.
  Verify: `source .venv/bin/activate && python -m hatch build`
- [ ] T086: Run a manual VS Code Chat smoke test with `@codegopher`.
  Verify: manual run in VS Code Extension Development Host
- [ ] T087: Run manual configured LLM endpoint and MCP server management smoke tests in VS Code.
  Verify: manual run in VS Code Extension Development Host
