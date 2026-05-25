# CodeGopher v0.10 Status - Mission Contracts And Skill-Led Task Ledgers

## Current State

- Plan docs created for v0.10.
- Core implementation complete locally.
- Scope is general runtime reliability, with documentation and security skills as first-class adopters.

## Initial Targets

- Add mission contracts and session task ledgers. Complete locally.
- Seed contract-backed TODOs for complex work and built-in skills. Complete locally.
- Preserve mission state through context injection and compaction. Complete locally.
- Gate chained-audit completion on report writer use and report artifact presence. Complete locally.
- Recover malformed tool-call JSON while a mission contract is active. Complete locally.
- Emit task lifecycle events and persist ledgers in TUI sessions. Complete locally.
- Update built-in doc and security skill guidance. Complete locally.

## Verification

- Focused unit and integration tests passed:
  `python -m pytest tests/unit/test_mission_contracts.py tests/unit/test_agent_loop.py tests/unit/test_events_session.py tests/unit/test_tui_session.py tests/unit/test_compaction.py tests/unit/test_skills.py tests/unit/test_static_audit_policy.py tests/integration/test_chained_vulns_safety.py`
- Focused Ruff passed for changed runtime and test files.
- Full Python test suite passed: `662 passed`.
- Full Ruff passed: `python -m ruff check .`.
- Mypy passed: `python -m mypy src`.
- Focused chained-audit rerun for prior misses passed; the retained in-repo record is
  `docs/plans/v0.10/report/SUMMARY.md`.

## Focused Prior-Miss Rerun

- Apps: `app-03-banking-service`, `app-46-charity-donations`.
- Model: `Qwen/Qwen3.6-35B-A3B`.
- Endpoint: `LOCAL_OPENAI_COMPATIBLE_ENDPOINT`.
- Result: both apps generated reports, called `write_chained_vulnerability_report`, and reached full recall.
- Aggregate recall: 4/4 chains and 12/12 components.
- Safety: no compromised runs; hygiene passed for both sanitized workspaces.

## Notes

- Active task details should live in the session task ledger, not persistent memory.
- Persistent memory remains explicit and user-approved.
- No public CLI command is planned for v0.10.
