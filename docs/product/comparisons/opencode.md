# CodeGopher And OpenCode Product Comparison

Reviewed: 2026-05-15

This note captures product ideas CodeGopher can borrow from OpenCode without losing CodeGopher's own shape: a Python-native, local, auditable, approval-first terminal agent.

## OpenCode Signals Worth Tracking

OpenCode presents itself as an open source coding agent available in the terminal, desktop app, and IDE. Its public product surface emphasizes:

- Terminal-first agent workflows.
- Plan and build modes.
- Fuzzy `@` file references.
- `/init`, `/undo`, `/redo`, `/share`, and custom slash commands.
- Configurable agents and subagents.
- Fine-grained permissions for tools and shell commands.
- LSP-aware code intelligence.
- Multi-session work in the same project.
- A server, SDK, plugins, and broader ecosystem hooks.
- Broad model/provider support, including local models.

## Best Ideas To Borrow

### 1. Plan And Build Modes

OpenCode makes planning a visible mode, not just an approval setting. CodeGopher already has `review`, `auto`, and `yolo`, but users would benefit from a clearer product distinction:

- `Plan`: read-only analysis, plans, investigation, and review.
- `Build`: approved edits, shell commands, tests, and implementation.

This exists in the roadmap as a later planning-mode idea, but it is important enough to consider pulling forward once the TUI is stable.

### 2. Excellent `@` Mentions

CodeGopher v0.2 already plans `@path` and `@glob` expansion. OpenCode's product lesson is that mentions should feel like a fast navigation primitive, not just parser syntax.

Good CodeGopher follow-ups:

- Fuzzy file picker from `@`.
- Preview before inclusion.
- Expansion summary before provider submission.
- Token or size estimate.
- Clear ignored, missing, binary, or out-of-root failures.

This is directly relevant to `T039` through `T045`.

### 3. `/init` Project Primer

OpenCode's `/init` creates project guidance for future sessions. CodeGopher could add a similar command that writes `AGENTS.md` or `.codegopher/PROJECT.md` after analyzing:

- Project structure.
- Test, lint, typecheck, and build commands.
- Coding conventions.
- Safety and approval notes.
- Common debugging workflows.

This would make CodeGopher more useful across repeated work without requiring full semantic memory.

### 4. Undo And Redo For Agent Changes

OpenCode's `/undo` and `/redo` reduce the fear of letting the agent edit files. CodeGopher's approval and prior-read rules are already strong, so an edit ledger would complement the safety story.

Potential shape:

- Track changed files per completed agent turn.
- Store enough patch data to reverse and reapply the turn.
- Show the original prompt after undo so the user can revise it.
- Keep shell side effects out of scope unless explicitly modeled.

### 5. Custom Markdown Commands

OpenCode supports custom command templates. CodeGopher could support project and user commands like:

- `.codegopher/commands/test.md`
- `.codegopher/commands/review.md`
- `.codegopher/commands/release-note.md`

Useful command features:

- `$ARGUMENTS` and positional arguments.
- `@file` references inside templates.
- Approved shell-output injection for commands like `git diff` or `pytest`.
- Optional command-level model, mode, or approval policy.

This fits naturally after the v0.2 slash command foundation.

### 6. Local Shareable Sessions

OpenCode has share links. CodeGopher should avoid hosted sharing at first and instead provide local, redacted exports:

- Markdown transcript.
- JSON transcript for tools.
- Prompt, response, tool-call, approval, diff, and test-output summaries.
- Provider/model metadata without secrets.

This would support debugging, team review, and issue reproduction while staying local-first.

### 7. Named Sessions And Resume

CodeGopher already plans session save/resume in v0.2. OpenCode's multi-session emphasis suggests making this more product-forward:

- Name sessions.
- Resume by recent project.
- Search previous session summaries.
- Show child or related sessions later if subagents are added.

The first version can remain simple JSON files, but the UI should make sessions feel like durable work, not temporary chat scrollback.

### 8. Agent Profiles

OpenCode exposes specialized agents and subagents. CodeGopher can start with a simpler, inspectable version:

- `planner`
- `builder`
- `reviewer`
- `debugger`
- `doc-writer`

Each profile could be Markdown or TOML-backed, with prompt, model, mode, and permission defaults. This is a smaller step than full subagent orchestration.

### 9. Fine-Grained Permission Policies

OpenCode's permission model supports `ask`, `allow`, and `deny` at a more detailed level. CodeGopher can preserve its approval-first design while adding project policies such as:

- Allow `git diff` and `git status`.
- Ask before `pytest`.
- Deny `git push`, deployment commands, or external directories.
- Ask before edits outside configured source directories.

This would make `auto` mode less blunt.

### 10. Diagnostics As Context

OpenCode highlights LSP intelligence. CodeGopher should probably start narrower and more Python-native:

- Structured `ruff` results.
- Structured `mypy` results.
- Structured `pyright` results when present.
- Test failure parsing.

Full LSP integration can wait until the product proves these lower-cost diagnostics are useful.

## Ideas To Avoid For Now

These OpenCode areas are useful, but probably not near-term priorities for CodeGopher:

- Desktop app.
- IDE extension.
- Hosted share links.
- Plugin runtime.
- Public model marketplace.
- Large provider catalog as a primary differentiator.
- Server/SDK architecture before the local CLI/TUI feels complete.

CodeGopher's best near-term wedge is not feature parity. It is a quieter promise: a local Python terminal agent that is easy to inspect, safe to approve, and pleasant to resume.

## Suggested Roadmap Impact

Near-term:

- Make `@` mentions excellent during v0.2.
- Add local session export to the session persistence milestone if scope allows.
- Keep `/init`, `/undo`, and custom commands as explicit v0.3 candidates.

Medium-term:

- Pull Plan/Build mode ahead of full subagents.
- Add permission policies before adding more risky tool surfaces.
- Use structured Python diagnostics before general LSP support.

Longer-term:

- Add agent profiles.
- Add subagent orchestration.
- Consider ACP, SDK, server, or plugin surfaces only after the core TUI workflow is strong.

## Sources

- OpenCode homepage: https://opencode.ai/
- OpenCode docs intro: https://opencode.ai/docs/
- OpenCode agents docs: https://opencode.ai/docs/agents/
- OpenCode commands docs: https://opencode.ai/docs/commands/
- OpenCode LSP docs: https://opencode.ai/docs/lsp/
- OpenCode server docs: https://opencode.ai/docs/server/
- OpenCode SDK docs: https://opencode.ai/docs/sdk/
- OpenCode plugins docs: https://opencode.ai/docs/plugins/
