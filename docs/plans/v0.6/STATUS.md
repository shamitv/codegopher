# CodeGopher v0.6 Implementation Status

Last reviewed: 2026-05-16

## Readiness Summary

- v0.6 is planned but not implemented.
- The release goal is a native VS Code Chat extension layer driven by a local `cgopher --events` JSONL protocol.
- No `extensions/vscode` package exists yet.
- No JSONL event protocol exists yet.
- Existing terminal and TUI workflows remain the baseline and must stay compatible.

Practical readiness estimate:

- Planning docs are present.
- Implementation work has not started.
- The first implementation step should define and test the protocol models before adding VS Code code.

## Current Repository State

| Area | Status | Notes |
|---|---|---|
| v0.1 baseline | Complete | Headless CLI, provider layer, tools, approvals, and tests exist. |
| v0.2 TUI | Complete | Textual TUI, approvals, slash commands, file mentions, shell passthrough, session persistence, and reasoning rendering exist. |
| v0.6 plan | Present | `PLAN.md` defines the VS Code extension direction. |
| v0.6 TODO | Present | `TODO.md` breaks work into commit-oriented tasks. |
| JSONL protocol | Not started | Needs typed Python models and CLI routing. |
| Agent session runner | Not started | Existing `run_agent` is one-shot and should remain compatible. |
| VS Code scaffold | Not started | No TypeScript package or extension manifest exists. |
| Chat participant | Not started | `@codegopher` is planned but not registered. |
| Approval bridge | Not started | Bidirectional approval over JSONL needs protocol and extension state. |
| Cancellation | Not started | Needs Python turn cancellation and VS Code token handling. |

## Verified Facts

- `docs/product/ROADMAP.md` keeps v0.3 for Context, Memory, And Skills.
- `docs/product/ROADMAP.md` keeps v0.4 for Providers And MCP.
- `docs/product/ROADMAP.md` keeps v0.5 for Repository Documentation And Static Security Skill Packs.
- `docs/product/ROADMAP.md` moves Advanced Coding Workflows to v0.7.
- Existing CLI options include `-p/--prompt`, `--model`, `--provider`, `--base-url`, `--approval-mode`, `--debug`, and `--json`.
- Existing approval modes are `review`, `auto`, and `yolo`.
- Existing core callbacks include text deltas, reasoning deltas, tool calls, tool results, approval requests, errors, and completion.
- Existing TUI owns an interactive `ToolContext` for a session.
- Existing session persistence is TUI-specific and should not be treated as the VS Code protocol.

## Immediate Blockers

- The protocol schema needs to be decided and tested before extension work can safely begin.
- The subprocess approval handshake needs careful design so Python remains authoritative while VS Code owns the user prompt.
- The session runner needs to support multiple turns without breaking the existing one-shot CLI path.

## Implementation Recommendation

Start with protocol models and Python `--events -p` one-shot streaming. Once the event stream is stable, add long-lived subprocess mode and only then scaffold the VS Code extension.
