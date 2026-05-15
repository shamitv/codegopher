# CodeGopher v0.1 Fine-Grained TODO

This checklist is intentionally small-step and commit-oriented. Each checkbox should normally be one commit. The goal is to make every meaningful state reversible without losing unrelated work.

Commit rules:

- Keep each commit focused on one behavior, one module, or one test slice.
- Prefer adding tests before or with the behavior they protect.
- Avoid mixed commits that combine refactors, dependencies, and feature behavior.
- Do not introduce provider API calls before the local CLI, config, and mock loop are stable.
- After every commit, run the smallest relevant verification command listed for that step.

## Milestone 0 - Runnable Skeleton

- [ ] C001: Add `src/codegopher/cli/main.py` with a minimal Click `app`.
  Verify: `PYTHONPATH=src python -m codegopher`
- [ ] C002: Make `python -m codegopher` print an alpha/help message when no prompt is provided.
  Verify: `PYTHONPATH=src python -m codegopher`
- [ ] C003: Add `-p/--prompt` option that echoes a dry-run response without model calls.
  Verify: `PYTHONPATH=src python -m codegopher -p "hello"`
- [ ] C004: Add `tests/unit/test_imports.py` covering package import and version.
  Verify: `python -m pytest tests/unit/test_imports.py`
- [ ] C005: Add CLI smoke tests for no-prompt and prompt dry-run behavior.
  Verify: `python -m pytest tests/unit/test_cli.py`
- [ ] C006: Remove or update any scaffold docstrings that claim unimplemented TUI behavior as current.
  Verify: `rg -n "TUI|MCP|memory|skills" src README.md docs`
- [ ] C007: Add a basic `CONTRIBUTING` note or docs section documenting commit/test expectations for v0.1 work.
  Verify: manual docs skim

## Milestone 0.5 - Sample Test Projects

- [ ] S001: Add `tests/fixtures/projects/README.md` describing fixture rules and mutation policy.
  Verify: manual docs skim
- [ ] S002: Add `tests/fixtures/projects/basic_python_package/README.md` with the fixture's test purpose.
  Verify: `Get-ChildItem -Recurse tests/fixtures/projects/basic_python_package`
- [ ] S003: Add `basic_python_package/pyproject.toml` with minimal package metadata.
  Verify: `python -c "import tomllib; tomllib.load(open('tests/fixtures/projects/basic_python_package/pyproject.toml','rb'))"`
- [ ] S004: Add `basic_python_package/src/sample_pkg/__init__.py` with a stable version string.
  Verify: `rg -n "__version__" tests/fixtures/projects/basic_python_package`
- [ ] S005: Add `basic_python_package/src/sample_pkg/math_utils.py` with two small pure functions.
  Verify: `rg -n "def " tests/fixtures/projects/basic_python_package/src/sample_pkg`
- [ ] S006: Add `basic_python_package/tests/test_math_utils.py` with passing tests.
  Verify: `rg -n "test_" tests/fixtures/projects/basic_python_package/tests`
- [ ] S007: Add `tests/fixtures/projects/buggy_cli_app/README.md` with the fixture's test purpose.
  Verify: manual docs skim
- [ ] S008: Add `buggy_cli_app/app.py` containing one intentional, documented failing behavior.
  Verify: `rg -n "TODO|BUG|intentional" tests/fixtures/projects/buggy_cli_app`
- [ ] S009: Add `buggy_cli_app/tests/test_app.py` that exposes the intentional failure.
  Verify: `rg -n "test_" tests/fixtures/projects/buggy_cli_app/tests`
- [ ] S010: Add `tests/fixtures/projects/configured_project/README.md` with config fixture purpose.
  Verify: manual docs skim
- [ ] S011: Add `configured_project/.codegopher/settings.toml` for project config precedence tests.
  Verify: `python -c "import tomllib; tomllib.load(open('tests/fixtures/projects/configured_project/.codegopher/settings.toml','rb'))"`
- [ ] S012: Add `configured_project/.codegopherignore` plus ignored and non-ignored files.
  Verify: `rg -n "ignored|visible" tests/fixtures/projects/configured_project`
- [ ] S013: Add `tests/fixtures/projects/edit_safety_project/README.md` with prior-read fixture purpose.
  Verify: manual docs skim
- [ ] S014: Add `edit_safety_project/src/existing.py` and an empty target directory for write/create tests.
  Verify: `Get-ChildItem -Recurse tests/fixtures/projects/edit_safety_project`
- [ ] S015: Add `tests/fixtures/helpers.py` with a copy-fixture-to-temp helper.
  Verify: `python -m pytest tests/unit/test_fixture_helpers.py`
- [ ] S016: Add tests that fixture copies are isolated from tracked fixture sources.
  Verify: `python -m pytest tests/unit/test_fixture_helpers.py`
- [ ] S017: Add sample project integrity tests that assert expected files exist.
  Verify: `python -m pytest tests/unit/test_sample_projects.py`
- [ ] S018: Document which later test suites should use each sample project.
  Verify: manual docs skim

## Milestone 1 - Shared Types And Errors

- [ ] C008: Add `core/errors.py` with base `CodeGopherError`.
  Verify: `python -m pytest`
- [ ] C009: Add specific errors for configuration, provider, tool, approval, and agent-loop failures.
  Verify: `python -m pytest`
- [ ] C010: Add `core/types.py` with `Message`, `ToolCall`, `ToolSchema`, and stream event types.
  Verify: `python -m pytest`
- [ ] C011: Add tests for public type imports from `core.types`.
  Verify: `python -m pytest tests/unit/test_core_types.py`
- [ ] C012: Add `utils/json.py` helper for safe JSON serialization of tool/provider payloads.
  Verify: `python -m pytest`
- [ ] C013: Add tests for malformed JSON handling.
  Verify: `python -m pytest tests/unit/test_json_utils.py`

## Milestone 2 - Configuration Foundation

- [ ] C014: Add `config/schema.py` with `ApprovalMode`, `ModelConfig`, `ProviderEntry`, and `Settings`.
  Verify: `python -m pytest`
- [ ] C015: Add schema tests for defaults.
  Verify: `python -m pytest tests/unit/test_config_schema.py`
- [ ] C016: Add schema tests for invalid approval mode and invalid token limits.
  Verify: `python -m pytest tests/unit/test_config_schema.py`
- [ ] C017: Add `config/loader.py` that returns default settings only.
  Verify: `python -m pytest tests/unit/test_config_loader.py`
- [ ] C018: Add user TOML loading from `~/.codegopher/settings.toml`.
  Verify: `python -m pytest tests/unit/test_config_loader.py`
- [ ] C019: Add project TOML loading from `.codegopher/settings.toml`.
  Verify: `python -m pytest tests/unit/test_config_loader.py`
- [ ] C020: Add deterministic merge behavior for nested config values.
  Verify: `python -m pytest tests/unit/test_config_loader.py`
- [ ] C021: Add environment variable overrides for model, provider, approval mode, and API key env names.
  Verify: `python -m pytest tests/unit/test_config_loader.py`
- [ ] C022: Add CLI override support in the loader.
  Verify: `python -m pytest tests/unit/test_config_loader.py tests/unit/test_cli.py`
- [ ] C023: Add clear error messages for malformed TOML.
  Verify: `python -m pytest tests/unit/test_config_loader.py`
- [ ] C024: Wire CLI options to `load_settings`.
  Verify: `PYTHONPATH=src python -m codegopher --approval-mode review`

## Milestone 3 - Approval Policy

- [ ] C025: Add `core/approval.py` with `should_prompt(mode, tool)`.
  Verify: `python -m pytest`
- [ ] C026: Add table-driven tests for `review`, `auto`, and `yolo`.
  Verify: `python -m pytest tests/unit/test_approval.py`
- [ ] C027: Add an approval request/result model for headless execution.
  Verify: `python -m pytest tests/unit/test_approval.py`
- [ ] C028: Add TTY approval prompt helper without integrating tool execution yet.
  Verify: `python -m pytest tests/unit/test_approval.py`
- [ ] C029: Add non-TTY denial behavior tests.
  Verify: `python -m pytest tests/unit/test_approval.py`

## Milestone 4 - Path And Prior-Read Tracking

- [ ] C030: Add `utils/paths.py` with canonical path resolution.
  Verify: `python -m pytest`
- [ ] C031: Add POSIX-style path canonicalization tests.
  Verify: `python -m pytest tests/unit/test_paths.py`
- [ ] C032: Add Windows-style case-normalization tests.
  Verify: `python -m pytest tests/unit/test_paths.py`
- [ ] C033: Add `tools/context.py` with session-scoped read and directory-inspection tracking.
  Verify: `python -m pytest`
- [ ] C034: Add tests for recording file reads.
  Verify: `python -m pytest tests/unit/test_tool_context.py`
- [ ] C035: Add tests for recording directory inspections.
  Verify: `python -m pytest tests/unit/test_tool_context.py`
- [ ] C036: Add prior-read checks for existing-file edits.
  Verify: `python -m pytest tests/unit/test_tool_context.py`
- [ ] C037: Add parent-inspection checks for new-file creation.
  Verify: `python -m pytest tests/unit/test_tool_context.py`
- [ ] C038: Add structured error messages for rejected writes.
  Verify: `python -m pytest tests/unit/test_tool_context.py`

## Milestone 5 - Tool Protocol And Registry

- [ ] C039: Add `tools/base.py` with `Tool`, `ToolResult`, and `ToolContext` definitions.
  Verify: `python -m pytest`
- [ ] C040: Add tests for `ToolResult` serialization.
  Verify: `python -m pytest tests/unit/test_tools_base.py`
- [ ] C041: Add `tools/registry.py` with register/get/list behavior.
  Verify: `python -m pytest`
- [ ] C042: Add registry duplicate-name tests.
  Verify: `python -m pytest tests/unit/test_tools_registry.py`
- [ ] C043: Add schema export from registered tools.
  Verify: `python -m pytest tests/unit/test_tools_registry.py`
- [ ] C044: Add default v0.1 registry factory with no concrete tools yet.
  Verify: `python -m pytest tests/unit/test_tools_registry.py`

## Milestone 6 - Read-Only File Tools

- [ ] C045: Add `tools/fs/read_file.py` with bounded UTF-8 reads.
  Verify: `python -m pytest tests/unit/test_read_file.py`
- [ ] C046: Add tests for line bounds in `read_file`.
  Verify: `python -m pytest tests/unit/test_read_file.py`
- [ ] C047: Add tests for missing files and binary/encoding failures.
  Verify: `python -m pytest tests/unit/test_read_file.py`
- [ ] C048: Make `read_file` record prior-read state.
  Verify: `python -m pytest tests/unit/test_read_file.py tests/unit/test_tool_context.py`
- [ ] C049: Add `tools/fs/list_dir.py`.
  Verify: `python -m pytest tests/unit/test_list_dir.py`
- [ ] C050: Make `list_dir` record inspected directories.
  Verify: `python -m pytest tests/unit/test_list_dir.py tests/unit/test_tool_context.py`
- [ ] C051: Add `tools/fs/glob_search.py` with basic glob support.
  Verify: `python -m pytest tests/unit/test_glob_search.py`
- [ ] C052: Add `.codegopherignore` parsing helper with simple gitignore-style patterns.
  Verify: `python -m pytest tests/unit/test_ignore.py`
- [ ] C053: Make `glob_search` respect `.codegopherignore`.
  Verify: `python -m pytest tests/unit/test_glob_search.py`
- [ ] C054: Add `tools/fs/grep_search.py` using Python fallback search.
  Verify: `python -m pytest tests/unit/test_grep_search.py`
- [ ] C055: Add optional `rg` acceleration behind the same `grep_search` output shape.
  Verify: `python -m pytest tests/unit/test_grep_search.py`
- [ ] C056: Add `tools/fs/read_many_files.py`.
  Verify: `python -m pytest tests/unit/test_read_many_files.py`
- [ ] C057: Make `read_many_files` record prior-read state for every file read.
  Verify: `python -m pytest tests/unit/test_read_many_files.py tests/unit/test_tool_context.py`
- [ ] C058: Register read-only file tools in the default registry.
  Verify: `python -m pytest tests/unit/test_tools_registry.py`

## Milestone 7 - Write File Tools

- [ ] C059: Add `tools/fs/write_file.py` create-only path with approval required.
  Verify: `python -m pytest tests/unit/test_write_file.py`
- [ ] C060: Gate new-file creation on parent directory inspection.
  Verify: `python -m pytest tests/unit/test_write_file.py`
- [ ] C061: Add existing-file replacement behavior gated by prior read.
  Verify: `python -m pytest tests/unit/test_write_file.py`
- [ ] C062: Add tests for rejected replacement without prior read.
  Verify: `python -m pytest tests/unit/test_write_file.py`
- [ ] C063: Add `tools/fs/edit_file.py` for exact text replacement.
  Verify: `python -m pytest tests/unit/test_edit_file.py`
- [ ] C064: Gate `edit_file` on prior read.
  Verify: `python -m pytest tests/unit/test_edit_file.py`
- [ ] C065: Add tests for missing match, multiple match, and no-op edit cases.
  Verify: `python -m pytest tests/unit/test_edit_file.py`
- [ ] C066: Register write tools in the default registry.
  Verify: `python -m pytest tests/unit/test_tools_registry.py`

## Milestone 8 - Shell Tool

- [ ] C067: Add `tools/shell/run_shell.py` with subprocess execution and timeout.
  Verify: `python -m pytest tests/unit/test_run_shell.py`
- [ ] C068: Add tests for successful command output capture.
  Verify: `python -m pytest tests/unit/test_run_shell.py`
- [ ] C069: Add tests for nonzero exit handling.
  Verify: `python -m pytest tests/unit/test_run_shell.py`
- [ ] C070: Add timeout cancellation tests.
  Verify: `python -m pytest tests/unit/test_run_shell.py`
- [ ] C071: Mark shell tool as approval required.
  Verify: `python -m pytest tests/unit/test_run_shell.py tests/unit/test_approval.py`
- [ ] C072: Register shell tool in the default registry.
  Verify: `python -m pytest tests/unit/test_tools_registry.py`

## Milestone 9 - Provider Foundation

- [ ] C073: Add `providers/base.py` with provider protocol and `ProviderCapabilities`.
  Verify: `python -m pytest tests/unit/test_provider_base.py`
- [ ] C074: Add provider registry with lookup by provider name.
  Verify: `python -m pytest tests/unit/test_provider_registry.py`
- [ ] C075: Add tests for capability failure when `tool_calls` is false.
  Verify: `python -m pytest tests/unit/test_provider_registry.py`
- [ ] C076: Add `providers/mock.py` for scripted tests.
  Verify: `python -m pytest tests/unit/test_mock_provider.py`
- [ ] C077: Add mock provider stream tests for text-only output.
  Verify: `python -m pytest tests/unit/test_mock_provider.py`
- [ ] C078: Add mock provider stream tests for tool-call output.
  Verify: `python -m pytest tests/unit/test_mock_provider.py`

## Milestone 10 - OpenAI-Compatible Provider

- [ ] C079: Add `providers/openai_compat.py` constructor and API-key resolution only.
  Verify: `python -m pytest tests/unit/test_openai_compat_provider.py`
- [ ] C080: Add missing API key error tests.
  Verify: `python -m pytest tests/unit/test_openai_compat_provider.py`
- [ ] C081: Add request-building tests for model, messages, tools, temperature, and token limit.
  Verify: `python -m pytest tests/unit/test_openai_compat_provider.py`
- [ ] C082: Add streaming text-delta parser with mocked chunks.
  Verify: `python -m pytest tests/unit/test_openai_compat_provider.py`
- [ ] C083: Add streaming tool-call parser with mocked chunks.
  Verify: `python -m pytest tests/unit/test_openai_compat_provider.py`
- [ ] C084: Add malformed tool-argument handling.
  Verify: `python -m pytest tests/unit/test_openai_compat_provider.py`
- [ ] C085: Add provider stream error normalization.
  Verify: `python -m pytest tests/unit/test_openai_compat_provider.py`
- [ ] C086: Register OpenAI-compatible provider in provider registry.
  Verify: `python -m pytest tests/unit/test_provider_registry.py`

## Milestone 11 - Conversation And Agent Loop

- [ ] C087: Add `core/conversation.py` with append user/assistant/tool result operations.
  Verify: `python -m pytest tests/unit/test_conversation.py`
- [ ] C088: Add tests for provider message conversion.
  Verify: `python -m pytest tests/unit/test_conversation.py`
- [ ] C089: Add `core/context.py` that builds system prompt and current messages.
  Verify: `python -m pytest tests/unit/test_context_builder.py`
- [ ] C090: Ensure system prompt only mentions implemented v0.1 features.
  Verify: `python -m pytest tests/unit/test_context_builder.py`
- [ ] C091: Add `core/agent.py` text-only loop using mock provider.
  Verify: `python -m pytest tests/unit/test_agent_loop.py`
- [ ] C092: Add max-iteration guard.
  Verify: `python -m pytest tests/unit/test_agent_loop.py`
- [ ] C093: Add tool-call execution path with read-only mock tool.
  Verify: `python -m pytest tests/unit/test_agent_loop.py`
- [ ] C094: Add approval denial path for required tools.
  Verify: `python -m pytest tests/unit/test_agent_loop.py`
- [ ] C095: Add prior-read rejection path through the agent loop.
  Verify: `python -m pytest tests/unit/test_agent_loop.py`
- [ ] C096: Add successful write-after-read path through the agent loop.
  Verify: `python -m pytest tests/unit/test_agent_loop.py`
- [ ] C097: Add structured final result object for CLI consumption.
  Verify: `python -m pytest tests/unit/test_agent_loop.py`

## Milestone 12 - Headless CLI Integration

- [ ] C098: Wire `-p/--prompt` to settings and mock provider behind a test flag or test injection seam.
  Verify: `python -m pytest tests/unit/test_cli.py`
- [ ] C099: Add stdin context append behavior.
  Verify: `python -m pytest tests/unit/test_cli.py`
- [ ] C100: Add `--json` output for dry-run/mock path.
  Verify: `python -m pytest tests/unit/test_cli.py`
- [ ] C101: Add CLI error handling for configuration errors.
  Verify: `python -m pytest tests/unit/test_cli.py`
- [ ] C102: Add CLI error handling for provider errors.
  Verify: `python -m pytest tests/unit/test_cli.py`
- [ ] C103: Add CLI wiring for real OpenAI-compatible provider.
  Verify: `python -m pytest tests/unit/test_cli.py`
- [ ] C104: Add non-TTY approval denial integration test.
  Verify: `python -m pytest tests/integration/test_headless_cli.py`
- [ ] C105: Add `--approval-mode yolo` integration test with a harmless temp-dir write.
  Verify: `python -m pytest tests/integration/test_headless_cli.py`

## Milestone 13 - Quality Gates

- [ ] C106: Make `ruff check src/ tests/` pass.
  Verify: `ruff check src/ tests/`
- [ ] C107: Make `mypy src/` pass.
  Verify: `mypy src/`
- [ ] C108: Make the full test suite pass.
  Verify: `python -m pytest`
- [ ] C109: Add Hatch script documentation for `hatch run test`, `lint`, and `typecheck`.
  Verify: manual docs skim
- [ ] C110: Add README status update showing which v0.1 features are implemented.
  Verify: manual docs skim
- [ ] C111: Add a changelog entry for the first runnable v0.1 skeleton.
  Verify: manual docs skim

## Milestone 14 - Pre-Release Hardening

- [ ] C112: Build the wheel locally.
  Verify: `python -m hatch build`
- [ ] C113: Install the built wheel in a clean virtual environment.
  Verify: `codegopher --help`
- [ ] C114: Run a smoke test through the installed `cgopher` entry point.
  Verify: `cgopher -p "hello" --json`
- [ ] C115: Audit docs for planned-vs-implemented wording.
  Verify: `rg -n "will|planned|implemented|currently" README.md docs`
- [ ] C116: Create a release checklist doc for the eventual PyPI publish.
  Verify: manual docs skim

## Defer Until After v0.1

- [ ] D001: Interactive Textual TUI.
- [ ] D002: Memory persistence.
- [ ] D003: Skills loader.
- [ ] D004: MCP client integration.
- [ ] D005: Anthropic provider.
- [ ] D006: Gemini provider using `google-genai`.
- [ ] D007: Web fetch and web search tools.
- [ ] D008: Git worktree helpers.
- [ ] D009: Sub-agent execution.
- [ ] D010: Docker sandboxing.
