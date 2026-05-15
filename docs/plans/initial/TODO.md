# CodeGopher v0.1 Fine-Grained TODO

This checklist is intentionally small-step and commit-oriented. Each checkbox should normally be one commit. The goal is to make every meaningful state reversible without losing unrelated work.

Commit rules:

- Keep each commit focused on one behavior, one module, or one test slice.
- Prefer adding tests before or with the behavior they protect.
- Avoid mixed commits that combine refactors, dependencies, and feature behavior.
- Do not introduce provider API calls before the local CLI, config, and mock loop are stable.
- After every commit, run the smallest relevant verification command listed for that step.

## Milestone 0 - Runnable Skeleton

- [x] C001: Add `src/codegopher/cli/main.py` with a minimal Click `app`.
  Verify: `PYTHONPATH=src python -m codegopher`
- [x] C002: Make `python -m codegopher` print an alpha/help message when no prompt is provided.
  Verify: `PYTHONPATH=src python -m codegopher`
- [x] C003: Add `-p/--prompt` option that echoes a dry-run response without model calls.
  Verify: `PYTHONPATH=src python -m codegopher -p "hello"`
- [x] C004: Add `tests/unit/test_imports.py` covering package import and version.
  Verify: `python -m pytest tests/unit/test_imports.py`
- [x] C005: Add CLI smoke tests for no-prompt and prompt dry-run behavior.
  Verify: `python -m pytest tests/unit/test_cli.py`
- [x] C006: Remove or update any scaffold docstrings that claim unimplemented TUI behavior as current.
  Verify: `rg -n "TUI|MCP|memory|skills" src README.md docs`
- [x] C007: Add a basic `CONTRIBUTING` note or docs section documenting commit/test expectations for v0.1 work.
  Verify: manual docs skim

## Milestone 0.5 - Sample Test Projects

- [x] S001: Add `tests/fixtures/projects/README.md` describing fixture rules and mutation policy.
  Verify: manual docs skim
- [x] S002: Add `tests/fixtures/projects/basic_python_package/README.md` with the fixture's test purpose.
  Verify: `Get-ChildItem -Recurse tests/fixtures/projects/basic_python_package`
- [x] S003: Add `basic_python_package/pyproject.toml` with minimal package metadata.
  Verify: `python -c "import tomllib; tomllib.load(open('tests/fixtures/projects/basic_python_package/pyproject.toml','rb'))"`
- [x] S004: Add `basic_python_package/src/sample_pkg/__init__.py` with a stable version string.
  Verify: `rg -n "__version__" tests/fixtures/projects/basic_python_package`
- [x] S005: Add `basic_python_package/src/sample_pkg/math_utils.py` with two small pure functions.
  Verify: `rg -n "def " tests/fixtures/projects/basic_python_package/src/sample_pkg`
- [x] S006: Add `basic_python_package/tests/test_math_utils.py` with passing tests.
  Verify: `rg -n "test_" tests/fixtures/projects/basic_python_package/tests`
- [x] S007: Add `tests/fixtures/projects/buggy_cli_app/README.md` with the fixture's test purpose.
  Verify: manual docs skim
- [x] S008: Add `buggy_cli_app/app.py` containing one intentional, documented failing behavior.
  Verify: `rg -n "TODO|BUG|intentional" tests/fixtures/projects/buggy_cli_app`
- [x] S009: Add `buggy_cli_app/tests/test_app.py` that exposes the intentional failure.
  Verify: `rg -n "test_" tests/fixtures/projects/buggy_cli_app/tests`
- [x] S010: Add `tests/fixtures/projects/configured_project/README.md` with config fixture purpose.
  Verify: manual docs skim
- [x] S011: Add `configured_project/.codegopher/settings.toml` for project config precedence tests.
  Verify: `python -c "import tomllib; tomllib.load(open('tests/fixtures/projects/configured_project/.codegopher/settings.toml','rb'))"`
- [x] S012: Add `configured_project/.codegopherignore` plus ignored and non-ignored files.
  Verify: `rg -n "ignored|visible" tests/fixtures/projects/configured_project`
- [x] S013: Add `tests/fixtures/projects/edit_safety_project/README.md` with prior-read fixture purpose.
  Verify: manual docs skim
- [x] S014: Add `edit_safety_project/src/existing.py` and an empty target directory for write/create tests.
  Verify: `Get-ChildItem -Recurse tests/fixtures/projects/edit_safety_project`
- [x] S015: Add `tests/fixtures/helpers.py` with a copy-fixture-to-temp helper.
  Verify: `python -m pytest tests/unit/test_fixture_helpers.py`
- [x] S016: Add tests that fixture copies are isolated from tracked fixture sources.
  Verify: `python -m pytest tests/unit/test_fixture_helpers.py`
- [x] S017: Add sample project integrity tests that assert expected files exist.
  Verify: `python -m pytest tests/unit/test_sample_projects.py`
- [x] S018: Document which later test suites should use each sample project.
  Verify: manual docs skim

## Milestone 1 - Shared Types And Errors

- [x] C008: Add `core/errors.py` with base `CodeGopherError`.
  Verify: `python -m pytest`
- [x] C009: Add specific errors for configuration, provider, tool, approval, and agent-loop failures.
  Verify: `python -m pytest`
- [x] C010: Add `core/types.py` with `Message`, `ToolCall`, `ToolSchema`, and stream event types.
  Verify: `python -m pytest`
- [x] C011: Add tests for public type imports from `core.types`.
  Verify: `python -m pytest tests/unit/test_core_types.py`
- [x] C012: Add `utils/json.py` helper for safe JSON serialization of tool/provider payloads.
  Verify: `python -m pytest`
- [x] C013: Add tests for malformed JSON handling.
  Verify: `python -m pytest tests/unit/test_json_utils.py`

## Milestone 2 - Configuration Foundation

- [x] C014: Add `config/schema.py` with `ApprovalMode`, `ModelConfig`, `ProviderEntry`, and `Settings`.
  Verify: `python -m pytest`
- [x] C015: Add schema tests for defaults.
  Verify: `python -m pytest tests/unit/test_config_schema.py`
- [x] C016: Add schema tests for invalid approval mode and invalid token limits.
  Verify: `python -m pytest tests/unit/test_config_schema.py`
- [x] C017: Add `config/loader.py` that returns default settings only.
  Verify: `python -m pytest tests/unit/test_config_loader.py`
- [x] C018: Add user TOML loading from `~/.codegopher/settings.toml`.
  Verify: `python -m pytest tests/unit/test_config_loader.py`
- [x] C019: Add project TOML loading from `.codegopher/settings.toml`.
  Verify: `python -m pytest tests/unit/test_config_loader.py`
- [x] C020: Add deterministic merge behavior for nested config values.
  Verify: `python -m pytest tests/unit/test_config_loader.py`
- [x] C021: Add environment variable overrides for model, provider, approval mode, and API key env names.
  Verify: `python -m pytest tests/unit/test_config_loader.py`
- [x] C022: Add CLI override support in the loader.
  Verify: `python -m pytest tests/unit/test_config_loader.py tests/unit/test_cli.py`
- [x] C023: Add clear error messages for malformed TOML.
  Verify: `python -m pytest tests/unit/test_config_loader.py`
- [x] C024: Wire CLI options to `load_settings`.
  Verify: `PYTHONPATH=src python -m codegopher --approval-mode review`

## Milestone 3 - Approval Policy

- [x] C025: Add `core/approval.py` with `should_prompt(mode, tool)`.
  Verify: `python -m pytest`
- [x] C026: Add table-driven tests for `review`, `auto`, and `yolo`.
  Verify: `python -m pytest tests/unit/test_approval.py`
- [x] C027: Add an approval request/result model for headless execution.
  Verify: `python -m pytest tests/unit/test_approval.py`
- [x] C028: Add TTY approval prompt helper without integrating tool execution yet.
  Verify: `python -m pytest tests/unit/test_approval.py`
- [x] C029: Add non-TTY denial behavior tests.
  Verify: `python -m pytest tests/unit/test_approval.py`

## Milestone 4 - Path And Prior-Read Tracking

- [x] C030: Add `utils/paths.py` with canonical path resolution.
  Verify: `python -m pytest`
- [x] C031: Add POSIX-style path canonicalization tests.
  Verify: `python -m pytest tests/unit/test_paths.py`
- [x] C032: Add Windows-style case-normalization tests.
  Verify: `python -m pytest tests/unit/test_paths.py`
- [x] C033: Add `tools/context.py` with session-scoped read and directory-inspection tracking.
  Verify: `python -m pytest`
- [x] C034: Add tests for recording file reads.
  Verify: `python -m pytest tests/unit/test_tool_context.py`
- [x] C035: Add tests for recording directory inspections.
  Verify: `python -m pytest tests/unit/test_tool_context.py`
- [x] C036: Add prior-read checks for existing-file edits.
  Verify: `python -m pytest tests/unit/test_tool_context.py`
- [x] C037: Add parent-inspection checks for new-file creation.
  Verify: `python -m pytest tests/unit/test_tool_context.py`
- [x] C038: Add structured error messages for rejected writes.
  Verify: `python -m pytest tests/unit/test_tool_context.py`

## Milestone 5 - Tool Protocol And Registry

- [x] C039: Add `tools/base.py` with `Tool`, `ToolResult`, and `ToolContext` definitions.
  Verify: `python -m pytest`
- [x] C040: Add tests for `ToolResult` serialization.
  Verify: `python -m pytest tests/unit/test_tools_base.py`
- [x] C041: Add `tools/registry.py` with register/get/list behavior.
  Verify: `python -m pytest`
- [x] C042: Add registry duplicate-name tests.
  Verify: `python -m pytest tests/unit/test_tools_registry.py`
- [x] C043: Add schema export from registered tools.
  Verify: `python -m pytest tests/unit/test_tools_registry.py`
- [x] C044: Add default v0.1 registry factory with no concrete tools yet.
  Verify: `python -m pytest tests/unit/test_tools_registry.py`

## Milestone 6 - Read-Only File Tools

- [x] C045: Add `tools/fs/read_file.py` with bounded UTF-8 reads.
  Verify: `python -m pytest tests/unit/test_read_file.py`
- [x] C046: Add tests for line bounds in `read_file`.
  Verify: `python -m pytest tests/unit/test_read_file.py`
- [x] C047: Add tests for missing files and binary/encoding failures.
  Verify: `python -m pytest tests/unit/test_read_file.py`
- [x] C048: Make `read_file` record prior-read state.
  Verify: `python -m pytest tests/unit/test_read_file.py tests/unit/test_tool_context.py`
- [x] C049: Add `tools/fs/list_dir.py`.
  Verify: `python -m pytest tests/unit/test_list_dir.py`
- [x] C050: Make `list_dir` record inspected directories.
  Verify: `python -m pytest tests/unit/test_list_dir.py tests/unit/test_tool_context.py`
- [x] C051: Add `tools/fs/glob_search.py` with basic glob support.
  Verify: `python -m pytest tests/unit/test_glob_search.py`
- [x] C052: Add `.codegopherignore` parsing helper with simple gitignore-style patterns.
  Verify: `python -m pytest tests/unit/test_ignore.py`
- [x] C053: Make `glob_search` respect `.codegopherignore`.
  Verify: `python -m pytest tests/unit/test_glob_search.py`
- [x] C054: Add `tools/fs/grep_search.py` using Python fallback search.
  Verify: `python -m pytest tests/unit/test_grep_search.py`
- [x] C055: Add optional `rg` acceleration behind the same `grep_search` output shape.
  Verify: `python -m pytest tests/unit/test_grep_search.py`
- [x] C056: Add `tools/fs/read_many_files.py`.
  Verify: `python -m pytest tests/unit/test_read_many_files.py`
- [x] C057: Make `read_many_files` record prior-read state for every file read.
  Verify: `python -m pytest tests/unit/test_read_many_files.py tests/unit/test_tool_context.py`
- [x] C058: Register read-only file tools in the default registry.
  Verify: `python -m pytest tests/unit/test_tools_registry.py`

## Milestone 7 - Write File Tools

- [x] C059: Add `tools/fs/write_file.py` create-only path with approval required.
  Verify: `python -m pytest tests/unit/test_write_file.py`
- [x] C060: Gate new-file creation on parent directory inspection.
  Verify: `python -m pytest tests/unit/test_write_file.py`
- [x] C061: Add existing-file replacement behavior gated by prior read.
  Verify: `python -m pytest tests/unit/test_write_file.py`
- [x] C062: Add tests for rejected replacement without prior read.
  Verify: `python -m pytest tests/unit/test_write_file.py`
- [x] C063: Add `tools/fs/edit_file.py` for exact text replacement.
  Verify: `python -m pytest tests/unit/test_edit_file.py`
- [x] C064: Gate `edit_file` on prior read.
  Verify: `python -m pytest tests/unit/test_edit_file.py`
- [x] C065: Add tests for missing match, multiple match, and no-op edit cases.
  Verify: `python -m pytest tests/unit/test_edit_file.py`
- [x] C066: Register write tools in the default registry.
  Verify: `python -m pytest tests/unit/test_tools_registry.py`

## Milestone 8 - Shell Tool

- [x] C067: Add `tools/shell/run_shell.py` with subprocess execution and timeout.
  Verify: `python -m pytest tests/unit/test_run_shell.py`
- [x] C068: Add tests for successful command output capture.
  Verify: `python -m pytest tests/unit/test_run_shell.py`
- [x] C069: Add tests for nonzero exit handling.
  Verify: `python -m pytest tests/unit/test_run_shell.py`
- [x] C070: Add timeout cancellation tests.
  Verify: `python -m pytest tests/unit/test_run_shell.py`
- [x] C071: Mark shell tool as approval required.
  Verify: `python -m pytest tests/unit/test_run_shell.py tests/unit/test_approval.py`
- [x] C072: Register shell tool in the default registry.
  Verify: `python -m pytest tests/unit/test_tools_registry.py`

## Milestone 9 - Provider Foundation

- [x] C073: Add `providers/base.py` with provider protocol and `ProviderCapabilities`.
  Verify: `python -m pytest tests/unit/test_provider_base.py`
- [x] C074: Add provider registry with lookup by provider name.
  Verify: `python -m pytest tests/unit/test_provider_registry.py`
- [x] C075: Add tests for capability failure when `tool_calls` is false.
  Verify: `python -m pytest tests/unit/test_provider_registry.py`
- [x] C076: Add `providers/mock.py` for scripted tests.
  Verify: `python -m pytest tests/unit/test_mock_provider.py`
- [x] C077: Add mock provider stream tests for text-only output.
  Verify: `python -m pytest tests/unit/test_mock_provider.py`
- [x] C078: Add mock provider stream tests for tool-call output.
  Verify: `python -m pytest tests/unit/test_mock_provider.py`

## Milestone 10 - OpenAI-Compatible Provider

- [x] C079: Add `providers/openai_compat.py` constructor and API-key resolution only.
  Verify: `python -m pytest tests/unit/test_openai_compat_provider.py`
- [x] C080: Add missing API key error tests.
  Verify: `python -m pytest tests/unit/test_openai_compat_provider.py`
- [x] C081: Add request-building tests for model, messages, tools, temperature, and token limit.
  Verify: `python -m pytest tests/unit/test_openai_compat_provider.py`
- [x] C082: Add streaming text-delta parser with mocked chunks.
  Verify: `python -m pytest tests/unit/test_openai_compat_provider.py`
- [x] C083: Add streaming tool-call parser with mocked chunks.
  Verify: `python -m pytest tests/unit/test_openai_compat_provider.py`
- [x] C084: Add malformed tool-argument handling.
  Verify: `python -m pytest tests/unit/test_openai_compat_provider.py`
- [x] C085: Add provider stream error normalization.
  Verify: `python -m pytest tests/unit/test_openai_compat_provider.py`
- [x] C086: Register OpenAI-compatible provider in provider registry.
  Verify: `python -m pytest tests/unit/test_provider_registry.py`

## Milestone 11 - Conversation And Agent Loop

- [x] C087: Add `core/conversation.py` with append user/assistant/tool result operations.
  Verify: `python -m pytest tests/unit/test_conversation.py`
- [x] C088: Add tests for provider message conversion.
  Verify: `python -m pytest tests/unit/test_conversation.py`
- [x] C089: Add `core/context.py` that builds system prompt and current messages.
  Verify: `python -m pytest tests/unit/test_context_builder.py`
- [x] C090: Ensure system prompt only mentions implemented v0.1 features.
  Verify: `python -m pytest tests/unit/test_context_builder.py`
- [x] C091: Add `core/agent.py` text-only loop using mock provider.
  Verify: `python -m pytest tests/unit/test_agent_loop.py`
- [x] C092: Add max-iteration guard.
  Verify: `python -m pytest tests/unit/test_agent_loop.py`
- [x] C093: Add tool-call execution path with read-only mock tool.
  Verify: `python -m pytest tests/unit/test_agent_loop.py`
- [x] C094: Add approval denial path for required tools.
  Verify: `python -m pytest tests/unit/test_agent_loop.py`
- [x] C095: Add prior-read rejection path through the agent loop.
  Verify: `python -m pytest tests/unit/test_agent_loop.py`
- [x] C096: Add successful write-after-read path through the agent loop.
  Verify: `python -m pytest tests/unit/test_agent_loop.py`
- [x] C097: Add structured final result object for CLI consumption.
  Verify: `python -m pytest tests/unit/test_agent_loop.py`

## Milestone 12 - Headless CLI Integration

- [x] C098: Wire `-p/--prompt` to settings and mock provider behind a test flag or test injection seam.
  Verify: `python -m pytest tests/unit/test_cli.py`
- [x] C099: Add stdin context append behavior.
  Verify: `python -m pytest tests/unit/test_cli.py`
- [x] C100: Add `--json` output for dry-run/mock path.
  Verify: `python -m pytest tests/unit/test_cli.py`
- [x] C101: Add CLI error handling for configuration errors.
  Verify: `python -m pytest tests/unit/test_cli.py`
- [x] C102: Add CLI error handling for provider errors.
  Verify: `python -m pytest tests/unit/test_cli.py`
- [x] C103: Add CLI wiring for real OpenAI-compatible provider.
  Verify: `python -m pytest tests/unit/test_cli.py`
- [x] C104: Add non-TTY approval denial integration test.
  Verify: `python -m pytest tests/integration/test_headless_cli.py`
- [x] C105: Add `--approval-mode yolo` integration test with a harmless temp-dir write.
  Verify: `python -m pytest tests/integration/test_headless_cli.py`

## Milestone 13 - Quality Gates

- [x] C106: Make `ruff check src/ tests/` pass.
  Verify: `ruff check src/ tests/`
- [x] C107: Make `mypy src/` pass.
  Verify: `mypy src/`
- [x] C108: Make the full test suite pass.
  Verify: `python -m pytest`
- [x] C109: Add Hatch script documentation for `hatch run test`, `lint`, and `typecheck`.
  Verify: manual docs skim
- [x] C110: Add README status update showing which v0.1 features are implemented.
  Verify: manual docs skim
- [x] C111: Add a changelog entry for the first runnable v0.1 skeleton.
  Verify: manual docs skim

## Milestone 14 - Pre-Release Hardening

- [x] C112: Build the wheel locally.
  Verify: `python -m hatch build`
- [x] C113: Install the built wheel in a clean virtual environment.
  Verify: `codegopher --help`
- [x] C114: Run a smoke test through the installed `cgopher` entry point.
  Verify: `cgopher -p "hello" --json`
- [x] C115: Audit docs for planned-vs-implemented wording.
  Verify: `rg -n "will|planned|implemented|currently" README.md docs`
- [x] C116: Create a release checklist doc for the eventual PyPI publish.
  Verify: manual docs skim

## Defer Until After v0.1

- [x] D001: Interactive Textual TUI.
- [x] D002: Memory persistence.
- [x] D003: Skills loader.
- [x] D004: MCP client integration.
- [x] D005: Anthropic provider.
- [x] D006: Gemini provider using `google-genai`.
- [x] D007: Web fetch and web search tools.
- [x] D008: Git worktree helpers.
- [x] D009: Sub-agent execution.
- [x] D010: Docker sandboxing.
