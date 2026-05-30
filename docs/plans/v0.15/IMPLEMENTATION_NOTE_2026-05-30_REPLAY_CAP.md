# v0.15 Implementation Note - Replay Message Cap For Local Proxy Stability

- Date: 2026-05-30
- Scope: first implementation step to reduce repeated full prompt re-processing
  observed on local llama-compatible endpoints.

## Why This Change Was Added

Proxy analysis showed large per-request input payloads with near-zero
`cached_input` reuse on the local path, which matches repeated server-side
context checkpoint invalidation and full prompt reprocessing.

Current runtime behavior sends full conversation history each turn unless
compaction has already occurred. For long chained-audit turns, this causes
prompt growth and low cache-hit rates on local servers.

## What Was Implemented

Added a configurable replay cap for provider message history:

- New setting: `context.max_replay_messages`
- Default: `null` (disabled; preserves existing behavior)
- Behavior when set: keep the most recent N replay messages, expanding across a
  tool-call boundary when needed so provider history does not start with an
  orphan tool result. The system prompt is still included every turn.

This provides an immediate way to bound prompt growth per turn while preserving
an opt-in rollout path.

## Files Changed

- `src/codegopher/config/schema.py`
  - added `ContextConfig.max_replay_messages: int | None`
- `src/codegopher/core/context.py`
  - added `max_replay_messages` parameter to `build_messages`
  - truncates replay history to a provider-valid recent suffix when configured
- `src/codegopher/core/agent.py`
  - passes `settings.context.max_replay_messages` into `build_messages`
  - uses the capped message view for automatic compaction budget checks
- `src/codegopher/tui/app.py`
  - uses the capped message view for context-budget display
- `tests/unit/test_context_builder.py`
  - added coverage for replay-cap truncation and tool-boundary behavior
- `tests/unit/test_config_schema.py`
  - added default/validation coverage for the new setting
- `tests/unit/test_agent_session.py`
  - added coverage that automatic compaction budget checks respect the replay cap

## Validation

Focused test commands executed:

```bash
.venv/bin/python -m pytest tests/unit/test_context_builder.py tests/unit/test_config_schema.py -q
.venv/bin/python -m pytest tests/unit/test_agent_session.py -q
.venv/bin/python -m pytest tests/unit/test_agent_loop.py -q
```

Result summary:

- `test_context_builder`: passed
- `test_config_schema`: passed
- `test_agent_session`: passed
- `test_agent_loop`: passed

## Operational Guidance

Recommended initial local setting for cache pressure reduction:

```toml
[context]
max_replay_messages = 20
```

If large prompt reprocessing remains frequent, reduce gradually (for example,
12-16) and compare proxy trends. The runtime may retain a few extra messages
when the cap lands inside a tool-call exchange:

- lower median input tokens
- increased `cached_input`
- reduced long-tail request durations

## Notes

- This is intentionally a minimal first step.
- No provider-specific transport behavior was changed in this increment.
- Full context replay remains available by leaving the setting unset.
