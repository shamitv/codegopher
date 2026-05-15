# CodeGopher v0.2 Fine-Grained TODO

This checklist is intentionally commit-oriented. Each checkbox should normally be one focused commit. Keep implementation work small enough that failures can be reverted without losing unrelated progress.

Commit rules:

- Preserve `cgopher -p/--prompt` behavior while adding interactive mode.
- Prefer tests before or with behavior.
- Keep TUI presentation code separate from the core agent loop.
- Reuse existing config, provider, tool, approval, and filesystem safety code.
- After every commit, run the smallest relevant verification command listed for that step.

## Milestone 0 - Planning And Dependency Setup

- [x] T001: Add `textual` as a runtime dependency and refresh packaging metadata if needed.
  Verify: `source .venv/bin/activate && python -m pip install -e ".[dev]"`
- [x] T002: Add an empty `codegopher.tui` package with clear placeholder docstrings.
  Verify: `python -m pytest tests/unit/test_imports.py`
- [x] T003: Add a TUI launcher function that can be imported without starting the app.
  Verify: `python -m pytest tests/unit/test_imports.py`
- [x] T004: Add CLI routing tests that prove `-p/--prompt` still uses headless mode.
  Verify: `python -m pytest tests/unit/test_cli.py`
- [x] T005: Add CLI routing tests for no-prompt TUI launch through a mocked launcher.
  Verify: `python -m pytest tests/unit/test_cli.py`
- [x] T006: Add CLI behavior for no-prompt non-TTY execution with a clear error.
  Verify: `python -m pytest tests/unit/test_cli.py`

## Milestone 1 - Minimal Textual App Shell

- [x] T007: Add a minimal Textual app class that starts and exits cleanly.
  Verify: `python -m pytest tests/unit/test_tui_app.py`
- [x] T008: Add the main layout: chat history region, input region, and status region.
  Verify: `python -m pytest tests/unit/test_tui_app.py`
- [x] T009: Add input submission handling that appends user messages to chat history.
  Verify: `python -m pytest tests/unit/test_tui_app.py`
- [x] T010: Add keyboard bindings for submit, quit, and focus input.
  Verify: `python -m pytest tests/unit/test_tui_app.py`
- [x] T011: Render startup state with active model, provider, approval mode, and cwd.
  Verify: `python -m pytest tests/unit/test_tui_app.py`
- [x] T012: Add a simple error banner or status message component.
  Verify: `python -m pytest tests/unit/test_tui_app.py`
- [x] T013: Wire `cgopher` without `-p` to launch the minimal app.
  Verify: `python -m pytest tests/unit/test_cli.py tests/unit/test_tui_app.py`

## Milestone 2 - Agent Stream-To-UI Wiring

- [x] T014: Define presentation callbacks or async events for text deltas, tool calls, tool results, errors, and completion.
  Verify: `python -m pytest tests/unit/test_agent_loop.py`
- [x] T015: Refactor the headless agent loop to emit callbacks/events without changing `AgentResult`.
  Verify: `python -m pytest tests/unit/test_agent_loop.py tests/integration/test_headless_cli.py`
- [x] T016: Add tests proving callback failures are reported clearly.
  Verify: `python -m pytest tests/unit/test_agent_loop.py`
- [x] T017: Stream assistant text into the TUI chat history as it arrives.
  Verify: `python -m pytest tests/unit/test_tui_agent.py`
- [x] T018: Disable input while an agent turn is running and re-enable it on completion.
  Verify: `python -m pytest tests/unit/test_tui_agent.py`
- [x] T019: Surface provider and agent-loop errors in the TUI status/error component.
  Verify: `python -m pytest tests/unit/test_tui_agent.py`
- [x] T020: Add an integration-style TUI test with `MockProvider` returning final text.
  Verify: `python -m pytest tests/unit/test_tui_agent.py`

## Milestone 3 - Tool Calls And Inline Approvals

- [x] T021: Render requested tool calls in chat history with tool name and argument summary.
  Verify: `python -m pytest tests/unit/test_tui_tools.py`
- [x] T022: Render completed tool results with success/error state.
  Verify: `python -m pytest tests/unit/test_tui_tools.py`
- [x] T023: Add an inline approval prompt component for required tools.
  Verify: `python -m pytest tests/unit/test_tui_approval.py`
- [x] T024: Route approval decisions from the TUI back into the agent turn.
  Verify: `python -m pytest tests/unit/test_tui_approval.py tests/unit/test_agent_loop.py`
- [x] T025: Support deny decisions with a reason returned to the model.
  Verify: `python -m pytest tests/unit/test_tui_approval.py`
- [x] T026: Respect `review`, `auto`, and `yolo` approval modes in the TUI.
  Verify: `python -m pytest tests/unit/test_tui_approval.py tests/unit/test_approval.py`
- [x] T027: Keep prior-read and parent-inspection failures visible as tool errors.
  Verify: `python -m pytest tests/unit/test_tui_tools.py tests/unit/test_write_file.py tests/unit/test_edit_file.py`
- [x] T028: Add a TUI test for a multi-iteration tool-call response.
  Verify: `python -m pytest tests/unit/test_tui_agent.py`

## Milestone 4 - Slash Commands

- [x] T029: Add slash-command parsing for input beginning with `/`.
  Verify: `python -m pytest tests/unit/test_tui_commands.py`
- [x] T030: Implement `/help` with command names and short descriptions.
  Verify: `python -m pytest tests/unit/test_tui_commands.py`
- [x] T031: Implement `/clear` to clear visible chat history without deleting persisted session data.
  Verify: `python -m pytest tests/unit/test_tui_commands.py`
- [x] T032: Implement `/model` display for the active model and provider.
  Verify: `python -m pytest tests/unit/test_tui_commands.py`
- [x] T033: Implement `/model NAME` to update the active model for future turns.
  Verify: `python -m pytest tests/unit/test_tui_commands.py tests/unit/test_config_schema.py`
- [x] T034: Implement `/mode` display for the active approval mode.
  Verify: `python -m pytest tests/unit/test_tui_commands.py`
- [x] T035: Implement `/mode review|auto|yolo` for future turns.
  Verify: `python -m pytest tests/unit/test_tui_commands.py tests/unit/test_approval.py`
- [x] T036: Implement `/stats` with turn count, tool count, approval count, and elapsed time.
  Verify: `python -m pytest tests/unit/test_tui_commands.py`
- [x] T037: Render unknown slash commands as user-facing errors.
  Verify: `python -m pytest tests/unit/test_tui_commands.py`
- [x] T038: Ensure slash commands do not call the provider unless explicitly intended.
  Verify: `python -m pytest tests/unit/test_tui_commands.py`

## Milestone 5 - File Mention Expansion

- [x] T039: Add a parser for `@path` and `@glob` mentions in submitted input.
  Verify: `python -m pytest tests/unit/test_tui_mentions.py`
- [x] T040: Resolve literal `@path` mentions relative to the session cwd.
  Verify: `python -m pytest tests/unit/test_tui_mentions.py tests/unit/test_read_file.py`
- [x] T041: Resolve glob mentions using existing glob/read-many behavior.
  Verify: `python -m pytest tests/unit/test_tui_mentions.py tests/unit/test_read_many_files.py`
- [x] T042: Respect `.codegopherignore` and project-root boundaries during expansion.
  Verify: `python -m pytest tests/unit/test_tui_mentions.py tests/unit/test_glob_search.py`
- [x] T043: Display mention expansion summaries before provider submission.
  Verify: `python -m pytest tests/unit/test_tui_mentions.py`
- [x] T044: Surface missing, binary, ignored, or out-of-root mention failures clearly.
  Verify: `python -m pytest tests/unit/test_tui_mentions.py`
- [x] T045: Mark successfully expanded files as prior reads for the session.
  Verify: `python -m pytest tests/unit/test_tui_mentions.py tests/unit/test_tool_context.py`

## Milestone 6 - Shell Passthrough

- [x] T046: Define the shell passthrough input syntax for the TUI.
  Verify: manual docs skim
- [x] T047: Parse shell passthrough input without sending it to the model first.
  Verify: `python -m pytest tests/unit/test_tui_shell.py`
- [x] T048: Require explicit approval before shell passthrough execution.
  Verify: `python -m pytest tests/unit/test_tui_shell.py tests/unit/test_approval.py`
- [x] T049: Execute approved shell passthrough through the existing shell tool.
  Verify: `python -m pytest tests/unit/test_tui_shell.py tests/unit/test_run_shell.py`
- [x] T050: Render shell stdout, stderr, exit code, and timeout states in chat history.
  Verify: `python -m pytest tests/unit/test_tui_shell.py`
- [x] T051: Ensure denied shell passthrough does not execute subprocesses.
  Verify: `python -m pytest tests/unit/test_tui_shell.py`

## Milestone 7 - Session Save And Resume

- [x] T052: Define the local session file format and storage location.
  Verify: `python -m pytest tests/unit/test_tui_session.py`
- [x] T053: Persist user and assistant messages after each completed turn.
  Verify: `python -m pytest tests/unit/test_tui_session.py`
- [x] T054: Persist tool-call summaries and tool-result summaries.
  Verify: `python -m pytest tests/unit/test_tui_session.py`
- [x] T055: Persist session metadata such as cwd, model, provider, approval mode, and created time.
  Verify: `python -m pytest tests/unit/test_tui_session.py`
- [x] T056: Do not persist API keys or raw environment values.
  Verify: `python -m pytest tests/unit/test_tui_session.py`
- [x] T057: Add a resume path that loads the most recent session for the same cwd.
  Verify: `python -m pytest tests/unit/test_tui_session.py`
- [x] T058: Render resumed messages in chat history on startup.
  Verify: `python -m pytest tests/unit/test_tui_session.py`
- [x] T059: Add user-facing errors for corrupt or incompatible session files.
  Verify: `python -m pytest tests/unit/test_tui_session.py`

## Milestone 8 - Thinking-Content Rendering

- [x] T060: Extend stream event types to distinguish reasoning deltas from answer text.
  Verify: `python -m pytest tests/unit/test_core_types.py`
- [x] T061: Parse provider `reasoning_content` into reasoning-specific events.
  Verify: `python -m pytest tests/unit/test_openai_compat_provider.py`
- [x] T062: Preserve headless final text without reasoning content.
  Verify: `python -m pytest tests/unit/test_agent_loop.py tests/integration/test_headless_cli.py`
- [x] T063: Show reasoning content in headless `--debug` output only.
  Verify: `python -m pytest tests/unit/test_cli.py`
- [x] T064: Render reasoning content collapsed by default in the TUI.
  Verify: `python -m pytest tests/unit/test_tui_reasoning.py`
- [x] T065: Add tests for mixed reasoning, answer text, and tool calls in one provider turn.
  Verify: `python -m pytest tests/unit/test_tui_reasoning.py tests/unit/test_agent_loop.py`

## Milestone 9 - Tests, Docs, And Release Readiness

- [x] T066: Update README with interactive TUI usage.
  Verify: `rg -n "cgopher|interactive|TUI" README.md`
- [ ] T067: Update product intro to describe v0.2 behavior as implemented.
  Verify: `rg -n "interactive|Textual|TUI" docs/product/INTRO.md`
- [ ] T068: Update v0.2 status doc with implemented components and remaining gaps.
  Verify: `rg -n "v0.2|Interactive Terminal" docs/plans/v0.2/STATUS.md`
- [ ] T069: Add or update release checklist items for interactive smoke testing.
  Verify: `rg -n "interactive|TUI|smoke" docs/release/CHECKLIST.md`
- [ ] T070: Run the complete unit and integration suite.
  Verify: `source .venv/bin/activate && python -m pytest`
- [ ] T071: Run lint and formatting checks.
  Verify: `source .venv/bin/activate && ruff check src/ tests/`
- [ ] T072: Run static type checking.
  Verify: `source .venv/bin/activate && mypy src/`
- [ ] T073: Build the distribution artifacts.
  Verify: `source .venv/bin/activate && python -m hatch build`
- [ ] T074: Add a manual TUI smoke-test note to the v0.2 status doc.
  Verify: manual run of `cgopher`
