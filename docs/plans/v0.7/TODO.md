# CodeGopher v0.7 Chained Vulnerability Detection TODO

This checklist is commit-oriented. Each checkbox represents a focused implementation or verification commit. Keep changes small enough that failures can be rolled back safely.

Commit rules:
- Complete, verify, and commit each task before starting the next task.
- Include the task ID in the commit message, for example `T012 Add chained audit tool policy`.
- Preserve the static-only security boundary.
- Verify with the smallest relevant command first, then run release gates at the end.

---

## Milestone 0 - Planning And Product Docs

- [x] T001: Create `docs/plans/v0.7/PLAN.md` with the chained vulnerability detection plan.
  Verify: `Test-Path docs/plans/v0.7/PLAN.md`
- [x] T002: Create `docs/plans/v0.7/TODO.md` with an implementation checklist.
  Verify: `Test-Path docs/plans/v0.7/TODO.md`
- [x] T003: Create `docs/plans/v0.7/STATUS.md` with initial status.
  Verify: `Test-Path docs/plans/v0.7/STATUS.md`
- [x] T004: Update `docs/product/ROADMAP.md` to make v0.7 "Chained Vulnerability Detection" and correct stale v0.6 status.
  Verify: `rg -n "Chained Vulnerability Detection|Done locally" docs/product/ROADMAP.md`
- [x] T005: Update `docs/product/INTRO.md` to mention chained audits, attack graph reports, and `chained-vulns`.
  Verify: `rg -n "chained-vulns|CHAINED_VULNERABILITIES_REVIEW" docs/product/INTRO.md`
- [x] T006: Update the v0.7 plan with the reviewed fixes: `all` pack, sub-agent/runtime contract, static-only enforcement, and UI/IDE verification.
  Verify: `rg -n "all|filtered registry|VS Code|Qwen" docs/plans/v0.7/PLAN.md`
- [x] T007: Update `docs/plans/v0.7/STATUS.md` with current state, verified facts, local-LLM gate, and remaining gates.
  Verify: `rg -n "Qwen/Qwen3.6-35B-A3B|filtered registry" docs/plans/v0.7/STATUS.md`

## Milestone 1 - Built-In Skill And Skill Packs

- [x] T008: Add `src/codegopher/skills/builtins/chained-vulnerability-static-audit/SKILL.md`.
  Verify: `Test-Path src/codegopher/skills/builtins/chained-vulnerability-static-audit/SKILL.md`
- [x] T009: Define front matter for name, description, and autoload keywords such as chained vulnerabilities and attack graph.
  Verify: `python -m pytest tests/unit/test_skills.py -k chained`
- [x] T010: Add `cgopher init --skill-pack chained-vulns`.
  Verify: `python -m pytest tests/unit/test_cli.py -k chained_vulns`
- [x] T011: Update `security` and `all` skill packs to include the chained audit skill.
  Verify: `python -m pytest tests/unit/test_cli.py -k "security_skill_pack or all_skill_pack"`
- [x] T012: Keep existing `repo-docs` behavior unchanged.
  Verify: `python -m pytest tests/unit/test_cli.py -k repo_docs`
- [x] T013: Add unit coverage that the built-in chained audit skill is discoverable and keeps static-only language.
  Verify: `python -m pytest tests/unit/test_skills.py`

## Milestone 2 - Static Audit Safety Policy

- [x] T014: Add a dedicated report-writing tool scoped to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`.
  Verify: `python -m pytest tests/unit/test_static_audit_policy.py -k report`
- [x] T015: Add a static audit registry factory that keeps read/list/search tools, `update_todo`, and the report writer only.
  Verify: `python -m pytest tests/unit/test_static_audit_policy.py -k registry`
- [x] T016: Trigger the static audit registry when `chained-vulnerability-static-audit` is explicitly mentioned.
  Verify: `python -m pytest tests/unit/test_static_audit_policy.py -k shell`
- [x] T017: Trigger the static audit registry when the skill autoloads from chained vulnerability keywords.
  Verify: `python -m pytest tests/unit/test_static_audit_policy.py -k report`
- [x] T018: Ensure unsafe model calls to missing tools return tool errors instead of crashing the agent turn.
  Verify: `python -m pytest tests/integration/test_chained_vulns_safety.py`
- [x] T019: Ensure shell, MCP-derived tools, save-memory, edit, and arbitrary write tools are absent from chained-audit tool schemas.
  Verify: `python -m pytest tests/unit/test_static_audit_policy.py`

## Milestone 3 - Attack Graph And Reporting

- [x] T020: Add security graph models for source, hop, sink, edge, severity, confidence, references, remediation, chain, and report.
  Verify: `python -m pytest tests/unit/test_security_graph.py`
- [x] T021: Validate attack graph edge references and code-reference line ranges.
  Verify: `python -m pytest tests/unit/test_security_graph.py`
- [x] T022: Add deterministic Mermaid flowchart rendering for attack chains.
  Verify: `python -m pytest tests/unit/test_mermaid_generator.py`
- [x] T023: Add Markdown report rendering with dashboard, methodology, Mermaid graphs, evidence, remediation, and unknowns.
  Verify: `python -m pytest tests/unit/test_report_writer.py`
- [x] T024: Add report writing to the default security report path.
  Verify: `python -m pytest tests/unit/test_report_writer.py -k write`

## Milestone 4 - Coordinator And Linker Scaffolding

- [x] T025: Add scan-plan targets for routing, auth, data, config, and jobs.
  Verify: `python -m pytest tests/unit/test_scan_coordinator.py`
- [x] T026: Add static-only weakness hunter prompt contract.
  Verify: `python -m pytest tests/unit/test_scan_coordinator.py -k prompt`
- [x] T027: Add structured scanner output validation.
  Verify: `python -m pytest tests/unit/test_chain_linker.py -k parse`
- [x] T028: Add linker prompt contract that requests structured chains without exploit payloads.
  Verify: `python -m pytest tests/unit/test_chain_linker.py -k prompt`
- [x] T029: Add deterministic source-hop-sink chain assembly scaffolding.
  Verify: `python -m pytest tests/unit/test_chain_linker.py -k builds`

## Milestone 5 - TUI And VS Code Invocation

- [x] T030: Add TUI `/audit --chain` command metadata and help text.
  Verify: `python -m pytest tests/unit/test_tui_commands.py -k help`
- [x] T031: Route `/audit --chain` into a normal agent prompt containing `@skill:chained-vulnerability-static-audit`.
  Verify: `python -m pytest tests/unit/test_tui_commands.py -k audit_chain`
- [x] T032: Reject invalid `/audit` arguments without calling the provider.
  Verify: `python -m pytest tests/unit/test_tui_commands.py -k audit_command`
- [x] T033: Add VS Code chat-controller coverage proving "scan for chained vulnerabilities" is forwarded as a normal prompt.
  Verify: `cd extensions/vscode && npm test -- --grep "chained vulnerability"`

## Milestone 6 - Integration Fixtures And Safety Tests

- [x] T034: Add a static fixture repository with an open redirect plus weak internal admin export chain.
  Verify: `Test-Path tests/fixtures/security/chained_flask_app/app.py`
- [x] T035: Add mocked integration coverage that builds a chain and writes a Mermaid report.
  Verify: `python -m pytest tests/integration/test_chained_vulns_integration.py`
- [x] T036: Add safety integration coverage for malicious `write_file` and `run_shell_command` calls.
  Verify: `python -m pytest tests/integration/test_chained_vulns_safety.py`
- [x] T037: Ensure the safe report writer still succeeds during chained-audit safety tests.
  Verify: `python -m pytest tests/integration/test_chained_vulns_safety.py -k report`

## Milestone 7 - Required Local LLM Verification

- [x] T038: Update real endpoint test to run against `http://192.168.96.5:8080/v1`.
  Verify: `rg -n "192.168.96.5:8080/v1" tests/integration/test_real_llm_endpoint.py`
- [x] T039: Configure the real endpoint test to use `Qwen/Qwen3.6-35B-A3B`, `chat_completions`, and `OPENAI_API_KEY=dummy-key`.
  Verify: `rg -n "Qwen/Qwen3.6-35B-A3B|dummy-key|chat_completions" tests/integration/test_real_llm_endpoint.py`
- [x] T040: Assert stripped final text equals `codegopher-smoke-ok`, no tools are used, and one iteration completes.
  Verify: `python -m pytest tests/integration/test_real_llm_endpoint.py`
- [x] T041: Do not rely on `/v1/models` for verification.
  Verify: `rg -n "/v1/models" tests/integration/test_real_llm_endpoint.py` returns no matches.

## Milestone 8 - Release Gates

- [x] T042: Run targeted Python tests for v0.7.
  Verify: `python -m pytest tests/unit/test_cli.py tests/unit/test_skills.py tests/unit/test_tui_commands.py tests/unit/test_static_audit_policy.py tests/unit/test_security_graph.py tests/unit/test_mermaid_generator.py tests/unit/test_report_writer.py tests/unit/test_scan_coordinator.py tests/unit/test_chain_linker.py tests/integration/test_chained_vulns_integration.py tests/integration/test_chained_vulns_safety.py`
- [x] T043: Run the full Python test suite.
  Verify: `python -m pytest`
- [x] T044: Run Python lint and typecheck.
  Verify: `python -m ruff check src tests && python -m mypy src`
- [x] T045: Run VS Code extension compile, lint, and tests.
  Verify: `cd extensions/vscode && npm run compile && npm run lint && npm test`
- [x] T046: Run required local LLM integration.
  Verify: `python -m pytest tests/integration/test_real_llm_endpoint.py`
- [x] T047: Update `docs/plans/v0.7/STATUS.md` to complete after all gates pass.
  Verify: `rg -n "Complete|Remaining Gates" docs/plans/v0.7/STATUS.md`
- [ ] T048: Run CI and release review before shipping v0.7.
  Verify: CI passes and release reviewer signs off.
