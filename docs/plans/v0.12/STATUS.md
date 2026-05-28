# CodeGopher v0.12 Status - Evidence-Led Task Memory

## Current State

- Implementation is complete locally.
- Planning docs exist for v0.12.
- Runtime episode memory, richer TODO state, chained-audit report gates, static-audit tool policy, provider usage fallback, and proxy active-run safety are implemented.
- Architecture docs are updated alongside the runtime changes.

## Implemented Changes

- Added task-local episode memory for file reads, searches, directory listings, TODO updates, report writes, tool errors, and final decisions.
- Added TODO statuses for blocked and cancelled work, plus reason, related-file, and evidence-reference metadata.
- Expanded the `update_todo` tool with update, block, unblock, and cancel actions.
- Injected episode memory into provider context and compaction prompts separately from persistent memory.
- Seeded mission TODOs with mission reasons and report artifact references.
- Added chained-audit report validation for Candidate Chain Ledger JSON, exact evidence shape, safe-control classification, and no-chain negative evidence.
- Hardened chained-audit static tools against hidden metadata paths, dotfiles, parent traversal, and answer-key search terms.
- Added Chat Completions `stream_options.include_usage` support with retry fallback.
- Changed benchmark proxy run startup to fail when any active run could contaminate stats.

## Verification

Focused verification passed:

```bash
.venv/bin/python -m pytest \
  tests/unit/test_todo_state.py \
  tests/unit/test_update_todo_tool.py \
  tests/unit/test_episode_state.py \
  tests/unit/test_context_builder.py \
  tests/unit/test_compaction.py \
  tests/unit/test_agent_session.py \
  tests/unit/test_mission_contracts.py \
  tests/unit/test_static_audit_policy.py \
  tests/unit/test_report_writer.py \
  tests/unit/test_openai_compat_provider.py \
  tests/unit/test_benchmark_proxy.py \
  tests/unit/test_agent_loop.py \
  tests/unit/test_events_session.py
```

Remaining verification before release:

- Sanitized secure-code-hunt validation on app-01 and at least one additional app.

Additional verification passed:

```bash
.venv/bin/python -m pytest
.venv/bin/python -m ruff check src tests docs/plans/v0.12 docs/arch
.venv/bin/python -m mypy src
```

Full pytest result: 724 passed.

Redaction checks passed for local endpoint URLs, temp paths, home paths, API key names, local dev keys, hidden manifests, and secure-code-hunt paths in the new v0.12 and architecture docs. The only text hits were generic architecture/product terms, not local or evaluator artifacts.

## Notes

- v0.12 remains a general runtime and skill-quality improvement pass, not app-01 tuning.
- Episode memory is task-local and not persisted through memory storage.
- Persistent memory remains explicit, local, and approval-gated.
- Static security skills remain source-only.
