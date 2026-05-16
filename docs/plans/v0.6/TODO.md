# CodeGopher v0.6 Fine-Grained TODO

This checklist is intentionally commit-oriented. Each checkbox should normally be one focused commit. Keep implementation work small enough that failures can be reverted without losing unrelated progress.

Commit rules:

- Preserve existing `cgopher`, `cgopher -p/--prompt`, `--json`, `--debug`, and TUI behavior.
- Keep Python authoritative for tools, approvals, provider behavior, and filesystem safety.
- Do not execute CodeGopher tools directly from TypeScript.
- Prefer protocol tests before VS Code UI work.
- After every commit, run the smallest relevant verification command listed for that step.

## Milestone 0 - Planning And Roadmap Setup

- [x] T001: Add the v0.6 roadmap entry for the VS Code extension layer.
  Verify: `rg -n "v0.6|VS Code Extension Layer|@codegopher" docs/product/ROADMAP.md`
- [x] T002: Add `docs/plans/v0.6/PLAN.md` with the implementation plan.
  Verify: `test -f docs/plans/v0.6/PLAN.md`
- [x] T003: Add `docs/plans/v0.6/TODO.md` with commit-oriented milestones.
  Verify: `test -f docs/plans/v0.6/TODO.md`
- [x] T004: Add `docs/plans/v0.6/STATUS.md` with initial status and blockers.
  Verify: `test -f docs/plans/v0.6/STATUS.md`

## Milestone 1 - JSONL Protocol Models

- [ ] T005: Add typed protocol models for common event and command fields.
  Verify: `python -m pytest tests/unit/test_events_protocol.py`
- [ ] T006: Add command models for `start_turn`, `approval_response`, `cancel_turn`, and `shutdown`.
  Verify: `python -m pytest tests/unit/test_events_protocol.py`
- [ ] T007: Add event models for session, turn, text, reasoning, tool, approval, error, and completion events.
  Verify: `python -m pytest tests/unit/test_events_protocol.py`
- [ ] T008: Add JSONL encode/decode helpers that reject malformed or unknown payloads clearly.
  Verify: `python -m pytest tests/unit/test_events_protocol.py`
- [ ] T009: Add protocol redaction tests for secrets and raw environment values.
  Verify: `python -m pytest tests/unit/test_events_protocol.py`

## Milestone 2 - Reusable Agent Session Runner

- [ ] T010: Add an agent session object that owns settings, provider, registry, cwd, and `ToolContext`.
  Verify: `python -m pytest tests/unit/test_agent_session.py`
- [ ] T011: Keep existing `run_agent` behavior compatible by delegating through the session runner where appropriate.
  Verify: `python -m pytest tests/unit/test_agent_loop.py tests/integration/test_headless_cli.py`
- [ ] T012: Add multi-turn session tests proving prior-read and directory-inspection state persists within a session.
  Verify: `python -m pytest tests/unit/test_agent_session.py tests/unit/test_tool_context.py`
- [ ] T013: Add callback-to-protocol event translation for text, reasoning, tools, approvals, errors, and completion.
  Verify: `python -m pytest tests/unit/test_agent_session.py tests/unit/test_events_protocol.py`
- [ ] T014: Add cancellation hooks for an active session turn.
  Verify: `python -m pytest tests/unit/test_agent_session.py`
- [ ] T015: Add structured session-runner errors for provider failure, agent-loop failure, cancellation, and bad approval state.
  Verify: `python -m pytest tests/unit/test_agent_session.py`

## Milestone 3 - `cgopher --events` CLI Mode

- [ ] T016: Add CLI routing for `--events -p PROMPT` without changing existing `--json` output.
  Verify: `python -m pytest tests/unit/test_cli.py tests/integration/test_headless_cli.py`
- [ ] T017: Emit JSONL events for one-shot text responses.
  Verify: `python -m pytest tests/integration/test_events_cli.py`
- [ ] T018: Emit JSONL events for reasoning deltas without including reasoning in final text.
  Verify: `python -m pytest tests/integration/test_events_cli.py tests/unit/test_agent_loop.py`
- [ ] T019: Emit tool-call and tool-result events for a multi-iteration response.
  Verify: `python -m pytest tests/integration/test_events_cli.py`
- [ ] T020: Support approval requests and stdin `approval_response` in one-shot events mode.
  Verify: `python -m pytest tests/integration/test_events_cli.py tests/unit/test_approval.py`
- [ ] T021: Add long-lived `cgopher --events` mode that accepts `start_turn` commands over stdin.
  Verify: `python -m pytest tests/integration/test_events_cli.py`
- [ ] T022: Support `cancel_turn` and `shutdown` commands in long-lived events mode.
  Verify: `python -m pytest tests/integration/test_events_cli.py`
- [ ] T023: Route human diagnostics to stderr while reserving stdout for protocol JSONL.
  Verify: `python -m pytest tests/integration/test_events_cli.py`
- [ ] T024: Preserve existing non-interactive no-prompt error when `--events` is not present.
  Verify: `python -m pytest tests/unit/test_cli.py`

## Milestone 4 - VS Code Extension Scaffold

- [ ] T025: Add `extensions/vscode/package.json` with extension metadata, commands, settings, and scripts.
  Verify: `cd extensions/vscode && npm install`
- [ ] T026: Add TypeScript, ESLint, and test configuration for the extension package.
  Verify: `cd extensions/vscode && npm run compile`
- [ ] T027: Add a minimal extension activation entry point.
  Verify: `cd extensions/vscode && npm test`
- [ ] T028: Add activation tests using the VS Code extension test runner.
  Verify: `cd extensions/vscode && npm test`
- [ ] T029: Add extension README notes for local development.
  Verify: `rg -n "CodeGopher|@codegopher|cgopher --events" extensions/vscode`

## Milestone 5 - Subprocess Protocol Client

- [ ] T030: Add a TypeScript JSONL parser with partial-line buffering.
  Verify: `cd extensions/vscode && npm test`
- [ ] T031: Add a CodeGopher subprocess client that launches `cgopher --events` in the workspace root.
  Verify: `cd extensions/vscode && npm test`
- [ ] T032: Add typed event routing for all protocol event types.
  Verify: `cd extensions/vscode && npm test`
- [ ] T033: Add pending request tracking for turns and approvals.
  Verify: `cd extensions/vscode && npm test`
- [ ] T034: Add stderr capture and structured subprocess exit errors.
  Verify: `cd extensions/vscode && npm test`
- [ ] T035: Add restart and shutdown lifecycle behavior.
  Verify: `cd extensions/vscode && npm test`
- [ ] T036: Add trace logging with redaction when `codegopher.traceProtocol` is enabled.
  Verify: `cd extensions/vscode && npm test`

## Milestone 6 - Chat Participant

- [ ] T037: Register the `@codegopher` chat participant in the extension manifest and activation code.
  Verify: `cd extensions/vscode && npm test`
- [ ] T038: Stream `text_delta` events into VS Code Chat markdown.
  Verify: `cd extensions/vscode && npm test`
- [ ] T039: Render `tool_call` and `tool_result` events as progress and compact chat summaries.
  Verify: `cd extensions/vscode && npm test`
- [ ] T040: Render provider and protocol errors as user-facing chat errors.
  Verify: `cd extensions/vscode && npm test`
- [ ] T041: Hide reasoning deltas by default while surfacing reasoning progress in trace/debug paths.
  Verify: `cd extensions/vscode && npm test`
- [ ] T042: Implement `/help` and `/status` chat commands.
  Verify: `cd extensions/vscode && npm test`
- [ ] T043: Implement `/restart` chat command.
  Verify: `cd extensions/vscode && npm test`

## Milestone 7 - Approval And Cancellation UX

- [ ] T044: Render approval requests with Approve and Deny chat buttons.
  Verify: `cd extensions/vscode && npm test`
- [ ] T045: Route Approve button clicks to `approval_response`.
  Verify: `cd extensions/vscode && npm test`
- [ ] T046: Route Deny button clicks to `approval_response` with a default denial reason.
  Verify: `cd extensions/vscode && npm test`
- [ ] T047: Prevent duplicate approval decisions for the same approval id.
  Verify: `cd extensions/vscode && npm test`
- [ ] T048: Respect VS Code cancellation tokens by sending `cancel_turn`.
  Verify: `cd extensions/vscode && npm test`
- [ ] T049: Confirm the subprocess can run another turn after cancellation or denial.
  Verify: `cd extensions/vscode && npm test`

## Milestone 8 - Settings, Errors, And Workspace Handling

- [ ] T050: Implement `codegopher.cliPath` resolution with clear missing-executable errors.
  Verify: `cd extensions/vscode && npm test`
- [ ] T051: Pass configured provider, model, base URL, and approval mode overrides to the CLI.
  Verify: `cd extensions/vscode && npm test`
- [ ] T052: Select the workspace root deterministically and show it in `/status`.
  Verify: `cd extensions/vscode && npm test`
- [ ] T053: Handle multi-root workspaces with a clear default and user-facing status.
  Verify: `cd extensions/vscode && npm test`
- [ ] T054: Add user-facing recovery guidance for subprocess crashes and invalid protocol messages.
  Verify: `cd extensions/vscode && npm test`
- [ ] T055: Add output-channel logging for extension lifecycle events.
  Verify: `cd extensions/vscode && npm test`

## Milestone 9 - Docs, Packaging, And Release Readiness

- [ ] T056: Update README with VS Code extension usage and setup.
  Verify: `rg -n "VS Code|@codegopher|--events" README.md`
- [ ] T057: Update product intro to mention the v0.6 IDE workflow.
  Verify: `rg -n "VS Code|IDE|@codegopher" docs/product/INTRO.md`
- [ ] T058: Update release checklist with VS Code extension smoke tests.
  Verify: `rg -n "VS Code|@codegopher|extension" docs/release/CHECKLIST.md`
- [ ] T059: Add local VSIX packaging instructions.
  Verify: `rg -n "vsix|package" extensions/vscode README.md docs`
- [ ] T060: Run the complete Python test suite.
  Verify: `source .venv/bin/activate && python -m pytest`
- [ ] T061: Run Python lint and type checks.
  Verify: `source .venv/bin/activate && ruff check src/ tests/ && mypy src/`
- [ ] T062: Run extension compile, lint, and tests.
  Verify: `cd extensions/vscode && npm run compile && npm run lint && npm test`
- [ ] T063: Build Python distribution artifacts.
  Verify: `source .venv/bin/activate && python -m hatch build`
- [ ] T064: Run a manual VS Code Chat smoke test with `@codegopher`.
  Verify: manual run in VS Code Extension Development Host
