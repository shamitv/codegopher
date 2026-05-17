# CodeGopher v0.3 Fine-Grained TODO

This checklist is intentionally commit-oriented. Each checkbox should normally be one focused commit. Keep implementation work small enough that failures can be reverted without losing unrelated progress.

Commit rules:

- Preserve existing `cgopher`, `cgopher -p/--prompt`, `--json`, `--debug`, and TUI behavior.
- Prefer tests before or with behavior.
- Keep memory, skill discovery, compaction, and TODO state inspectable.
- Do not add executable plugins in v0.3.
- Do not persist API keys or raw environment values.
- Reuse existing approval, filesystem safety, `.codegopherignore`, config, provider, and tool code.
- After every commit, run the smallest relevant verification command listed for that step.

## Milestone 0 - Planning And Branch Setup

- [x] T001: Add `docs/plans/v0.3/PLAN.md` with the v0.3 implementation direction.
  Verify: `test -f docs/plans/v0.3/PLAN.md`
- [x] T002: Add `docs/plans/v0.3/TODO.md` with commit-sized implementation tasks.
  Verify: `test -f docs/plans/v0.3/TODO.md`
- [x] T003: Add `docs/plans/v0.3/STATUS.md` with initial status and blockers.
  Verify: `test -f docs/plans/v0.3/STATUS.md`
- [x] T004: Confirm local `.codegopher/` config remains ignored and outside committed files.
  Verify: `git status --ignored --short .codegopher .gitignore`

## Milestone 1 - Config And Data Types

- [x] T005: Add settings schema for context budget defaults, including warning and compaction thresholds.
  Verify: `python -m pytest tests/unit/test_config_schema.py`
- [x] T006: Add settings schema for memory enablement and storage defaults.
  Verify: `python -m pytest tests/unit/test_config_schema.py`
- [x] T007: Add settings schema for skill discovery locations and loading defaults.
  Verify: `python -m pytest tests/unit/test_config_schema.py`
- [x] T008: Add settings schema for session TODO enablement.
  Verify: `python -m pytest tests/unit/test_config_schema.py`
- [x] T009: Add typed data models for memory entries, skill metadata, compaction entries, and TODO items.
  Verify: `python -m pytest tests/unit/test_core_types.py`
- [x] T010: Add validation tests for invalid thresholds, invalid memory scopes, and malformed TODO statuses.
  Verify: `python -m pytest tests/unit/test_config_schema.py tests/unit/test_core_types.py`

## Milestone 2 - Reusable Session And Context Runner

- [x] T011: Add a reusable session/context runner that owns provider-ready conversation history, including text-only multi-turn history, tool-call history, callbacks, errors, and isolated sessions.
  Verify: `python -m pytest tests/unit/test_agent_session.py`
- [x] T012: Preserve `run_agent` import compatibility and one-shot behavior, including no history leakage between calls.
  Verify: `python -m pytest tests/unit/test_agent_loop.py tests/integration/test_headless_cli.py`
- [x] T013: Move TUI agent turns onto the session/context runner without changing visible behavior, including `/clear`, slash command, mention expansion, and tool-history regressions.
  Verify: `python -m pytest tests/unit/test_tui_agent.py tests/unit/test_tui_session.py tests/unit/test_tui_mentions.py`
- [x] T014: Persist enough session metadata to resume provider-ready context safely, including legacy session compatibility and provider-message validation.
  Verify: `python -m pytest tests/unit/test_tui_session.py tests/unit/test_agent_session.py`
- [x] T015: Ensure prior-read and directory-inspection state remains session-scoped, without restoring stale access grants after resume.
  Verify: `python -m pytest tests/unit/test_agent_session.py tests/unit/test_tool_context.py tests/unit/test_tui_session.py`
- [x] T016: Add tests proving multi-turn TUI context reaches the provider, including integration-style resume/context and resume safety coverage.
  Verify: `python -m pytest tests/unit/test_tui_agent.py tests/unit/test_agent_session.py tests/integration/test_tui_context_resume.py`

## Milestone 3 - Context Budget Tracking

- [x] T017: Add a token-counting helper using `tiktoken` with a deterministic fallback.
  Verify: `python -m pytest tests/unit/test_context_budget.py`
- [x] T018: Read provider `context_window` from the selected provider entry.
  Verify: `python -m pytest tests/unit/test_context_budget.py tests/unit/test_config_loader.py`
- [x] T019: Add warning and compaction threshold calculations with defaults around 70 and 80 percent.
  Verify: `python -m pytest tests/unit/test_context_budget.py`
- [x] T020: Surface context budget state in TUI status or `/stats`.
  Verify: `python -m pytest tests/unit/test_tui_commands.py`
- [x] T021: Add tests for missing context windows and small-window edge cases.
  Verify: `python -m pytest tests/unit/test_context_budget.py`

## Milestone 4 - Manual And Automatic Compaction

- [x] T022: Add a compaction prompt builder that summarizes older conversation and tool context.
  Verify: `python -m pytest tests/unit/test_compaction.py`
- [x] T023: Add manual `/compact [instructions]` command parsing and validation.
  Verify: `python -m pytest tests/unit/test_tui_commands.py`
- [x] T024: Run manual compaction through the provider and store a visible compaction entry.
  Verify: `python -m pytest tests/unit/test_tui_compaction.py tests/unit/test_agent_session.py`
- [x] T025: Add automatic compaction before a turn that would exceed the threshold.
  Verify: `python -m pytest tests/unit/test_compaction.py tests/unit/test_agent_session.py`
- [x] T026: Preserve recent turns verbatim after compaction.
  Verify: `python -m pytest tests/unit/test_compaction.py`
- [x] T027: Include active TODO state, selected memories, and loaded skills in compaction behavior.
  Verify: `python -m pytest tests/unit/test_compaction.py`
- [x] T028: Surface compaction failures clearly without losing the current session.
  Verify: `python -m pytest tests/unit/test_tui_compaction.py`

## Milestone 5 - Memory Store And `save_memory`

- [x] T029: Add a local memory store rooted under CodeGopher data home.
  Verify: `python -m pytest tests/unit/test_memory_store.py`
- [x] T030: Add session memory keyed by session id.
  Verify: `python -m pytest tests/unit/test_memory_store.py`
- [x] T031: Add project memory keyed by canonical cwd hash.
  Verify: `python -m pytest tests/unit/test_memory_store.py`
- [x] T032: Add memory CRUD operations with stable ids and timestamps.
  Verify: `python -m pytest tests/unit/test_memory_store.py`
- [x] T033: Add safety tests proving memories do not persist API keys or raw environment values.
  Verify: `python -m pytest tests/unit/test_memory_store.py tests/unit/test_tui_session.py`
- [x] T034: Add approval-gated `save_memory` tool.
  Verify: `python -m pytest tests/unit/test_save_memory_tool.py tests/unit/test_approval.py`
- [x] T035: Register `save_memory` in the default tool registry.
  Verify: `python -m pytest tests/unit/test_tools_registry.py tests/unit/test_context_builder.py`
- [ ] T036: Feed selected memories into provider context.
  Verify: `python -m pytest tests/unit/test_context_builder.py tests/unit/test_agent_session.py`

## Milestone 6 - TUI Memory Commands And Transparency

- [ ] T037: Add `/memory` command to list session and project memories.
  Verify: `python -m pytest tests/unit/test_tui_memory.py tests/unit/test_tui_commands.py`
- [ ] T038: Add `/forget ID` command with approval or confirmation behavior.
  Verify: `python -m pytest tests/unit/test_tui_memory.py`
- [ ] T039: Show memory save/delete events in chat history.
  Verify: `python -m pytest tests/unit/test_tui_memory.py`
- [ ] T040: Show active memory count in status or `/stats`.
  Verify: `python -m pytest tests/unit/test_tui_memory.py tests/unit/test_tui_commands.py`
- [ ] T041: Add resume tests proving session memory remains associated with the resumed session.
  Verify: `python -m pytest tests/unit/test_tui_memory.py tests/unit/test_tui_session.py`

## Milestone 7 - Markdown Skill Discovery And Loading

- [ ] T042: Add skill discovery for project `.codegopher/skills/*/SKILL.md`.
  Verify: `python -m pytest tests/unit/test_skills.py`
- [ ] T043: Add skill discovery for user `~/.codegopher/skills/*/SKILL.md`.
  Verify: `python -m pytest tests/unit/test_skills.py`
- [ ] T044: Add built-in package skill discovery.
  Verify: `python -m pytest tests/unit/test_skills.py tests/unit/test_imports.py`
- [ ] T045: Parse simple skill metadata and Markdown content.
  Verify: `python -m pytest tests/unit/test_skills.py`
- [ ] T046: Add progressive skill loading by explicit mention or keyword match.
  Verify: `python -m pytest tests/unit/test_skills.py tests/unit/test_agent_session.py`
- [ ] T047: Feed loaded skill Markdown into provider context.
  Verify: `python -m pytest tests/unit/test_context_builder.py tests/unit/test_skills.py`
- [ ] T048: Add `/skills` command to list discovered and loaded skills.
  Verify: `python -m pytest tests/unit/test_tui_skills.py tests/unit/test_tui_commands.py`
- [ ] T049: Add safety tests proving skills are read-only context and not executable plugins.
  Verify: `python -m pytest tests/unit/test_skills.py`

## Milestone 8 - Session TODO State

- [ ] T050: Add TODO state models and store.
  Verify: `python -m pytest tests/unit/test_todo_state.py`
- [ ] T051: Add `/todo` command to display current TODO state.
  Verify: `python -m pytest tests/unit/test_tui_todo.py tests/unit/test_tui_commands.py`
- [ ] T052: Add `/todo add TEXT` command.
  Verify: `python -m pytest tests/unit/test_tui_todo.py`
- [ ] T053: Add `/todo done ID` command.
  Verify: `python -m pytest tests/unit/test_tui_todo.py`
- [ ] T054: Add model-facing `update_todo` tool.
  Verify: `python -m pytest tests/unit/test_update_todo_tool.py tests/unit/test_tools_registry.py`
- [ ] T055: Feed active TODO state into provider context.
  Verify: `python -m pytest tests/unit/test_context_builder.py tests/unit/test_todo_state.py`
- [ ] T056: Persist TODO state with session resume.
  Verify: `python -m pytest tests/unit/test_tui_todo.py tests/unit/test_tui_session.py`
- [ ] T057: Include TODO state in compaction behavior.
  Verify: `python -m pytest tests/unit/test_compaction.py tests/unit/test_todo_state.py`

## Milestone 9 - Docs, Real Endpoint Smoke, And Release Readiness

- [ ] T058: Update README with v0.3 context, memory, skills, and TODO usage.
  Verify: `rg -n "memory|skills|compact|todo" README.md`
- [ ] T059: Update product intro to describe implemented v0.3 behavior.
  Verify: `rg -n "memory|skills|compact|todo" docs/product/INTRO.md`
- [ ] T060: Update v0.3 status doc with implemented components and remaining gaps.
  Verify: `rg -n "v0.3|Context|Memory|Skills" docs/plans/v0.3/STATUS.md`
- [ ] T061: Update release checklist with v0.3 smoke tests.
  Verify: `rg -n "memory|skills|compact|todo" docs/release/CHECKLIST.md`
- [ ] T062: Run a real OpenAI-compatible endpoint smoke test using local ignored config.
  Verify: manual run of `cgopher -p "hello"` with local endpoint and dummy key
- [ ] T063: Run the complete unit and integration suite.
  Verify: `source .venv/bin/activate && python -m pytest`
- [ ] T064: Run lint and formatting checks.
  Verify: `source .venv/bin/activate && ruff check src/ tests/`
- [ ] T065: Run static type checking.
  Verify: `source .venv/bin/activate && mypy src/`
- [ ] T066: Build the distribution artifacts.
  Verify: `source .venv/bin/activate && python -m hatch build`
- [ ] T067: Add a manual TUI v0.3 smoke-test note to the v0.3 status doc.
  Verify: manual run of `cgopher`
