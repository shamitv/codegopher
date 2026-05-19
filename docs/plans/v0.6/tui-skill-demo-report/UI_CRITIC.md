# CodeGopher UI Critic: TUI And VS Code

Date: 2026-05-19

Evidence reviewed:

- TUI screenshots in this folder: [startup/help](screenshots/01-tui-startup-help.png), [model/mode/stats](screenshots/02-tui-model-mode-stats.png), [exact smoke](screenshots/03-tui-exact-smoke.png), [domain docs](screenshots/04-tui-repo-domain-docs.png), [tech docs](screenshots/05-tui-repo-tech-docs.png)
- VS Code smoke report screenshots: [status](../vscode-skill-demo-report/screenshots/01-vscode-status.png), [endpoint smoke](../vscode-skill-demo-report/screenshots/02-endpoint-smoke.png), [domain docs](../vscode-skill-demo-report/screenshots/03-repo-domain-docs.png), [tech docs](../vscode-skill-demo-report/screenshots/04-repo-tech-docs.png)

## Overall Read

CodeGopher's strongest UI trait is consistency of execution semantics. The TUI, headless CLI, and VS Code extension all route through the same Python engine, provider config, approval model, tool execution, and skill system. That makes the product feel coherent and safer than maintaining separate agent runtimes per surface.

The main weakness is presentation density. Long Markdown-heavy responses, tool traces, and status strings are technically visible, but not yet shaped into review-friendly UI objects. The product works; the next UX lift is making important state easier to scan while keeping the terminal-first personality.

## Strengths

| Area | What Works |
|---|---|
| TUI startup | The header, command area, and input field make it obvious that the session is interactive. |
| TUI slash commands | `/help`, `/model`, `/mode`, and `/stats` give local control without provider calls. |
| TUI safety | Review mode is visible, and shell/tool approval UI exists in the same surface as the chat. |
| TUI skills | Built-in skills work through normal prompt flow, including `@skill:repo-domain-docs` and `@skill:repo-tech-docs`. |
| VS Code chat | Native `@codegopher` fits the IDE mental model and avoids a custom webview too early. |
| VS Code status | `/status` exposes workspace, CLI, provider/model, approval mode, and subprocess state clearly. |
| Secret hygiene | Endpoint and model are visible; API key value is not shown. |

## Findings

| Priority | Finding | Evidence | Recommendation |
|---|---|---|---|
| P1 | TUI Markdown is readable but not rendered as structured UI. Tables, headings, and lists are plain text, so skill output becomes visually dense. | Domain and tech screenshots show raw Markdown markers and wrapped table rows. | Add Markdown-aware message rendering or a lightweight formatter for headings, bullets, tables, and code blocks. |
| P1 | Long TUI skill output lands at the final scroll position, which can hide the report's beginning in evidence and during review. | The original unbounded domain run ended at the tail of the report; the final evidence needed bounded prompts. | Add a post-turn affordance to jump to the start of the last assistant message, or render each assistant turn as a collapsible block. |
| P1 | TUI lacks a single `/status` equivalent to VS Code's `@codegopher /status`. Users must combine `/model`, `/mode`, and `/stats`, and endpoint/API key env are not shown. | TUI evidence needs three commands to approximate status. VS Code has one status command. | Add `/status` in TUI with model, provider, base URL when configured, API family, API key env name, approval mode, cwd, data home, and MCP state, with secrets redacted. |
| P2 | Reasoning display still consumes chat space even when labelled collapsed. | Exact-smoke screenshot shows a reasoning block before the final answer. | Default to a one-line expandable reasoning affordance, or hide reasoning unless the user asks to expand it. |
| P2 | Tool traces are transparent but noisy for documentation skills. | Free-form skill runs produced many `Tool requested` and `Tool completed` messages. | Group tool activity under a compact per-turn "tools used" summary, with expansion for details. |
| P2 | VS Code model selection can retain stale custom model entries. | Prior VS Code smoke required refreshing/selecting the new `Qwen3.6...` model after a stale `Qwen3.5...` entry. | Add a visible model refresh or mismatch warning when configured model and selected chat model differ. |
| P3 | Screenshotability is fragile on macOS. | Shell `screencapture` failed due TCC; Textual export was needed for TUI evidence. | Add a documented smoke-evidence command that exports current TUI state to PNG/SVG without OS screen capture permissions. |

## Cross-Surface Consistency

| Capability | TUI | VS Code | Gap |
|---|---|---|---|
| Status | Split across `/model`, `/mode`, `/stats` | Unified `@codegopher /status` | Add TUI `/status`. |
| Restart | Relaunch terminal session manually | `@codegopher /restart` and command palette restart | Add a TUI `/restart` only if it can safely rebuild provider/MCP state. |
| Endpoint visibility | Indirect through launch command/config | `CodeGopher: View LLM Endpoint` | Add redacted endpoint display in TUI status. |
| Skill prompts | `@skill:ID` works in chat input | `@skill:ID` works in VS Code chat | Good; preserve syntax. |
| Approval | Inline Textual approval panel | Native VS Code approval buttons | Good; keep semantics aligned. |
| Evidence export | Textual live screenshot API works, but is not productized | VS Code depends on app/OS capture | Provide first-class smoke artifact export for both. |

## Recommended Next UI Work

1. Add TUI `/status` and align its fields with VS Code `@codegopher /status`.
2. Improve TUI message rendering for Markdown-heavy skill outputs.
3. Compact tool traces by default while preserving full transparency on expansion.
4. Hide or truly collapse reasoning output unless explicitly expanded.
5. Add a first-class smoke evidence export path for TUI and VS Code demos.
6. Teach built-in repo-documentation skills to avoid excluded benchmark ground-truth files by default.

These are UI improvements, not release blockers for the tested v0.6 behavior. The current surfaces are functional and consistent enough for smoke validation; the next pass should focus on scanability, evidence capture, and cross-surface command parity.
