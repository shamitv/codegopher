# CodeGopher v0.3 Implementation Plan

This plan covers the v0.3 implementation slice: context, memory, Markdown skills, and session TODO state on top of the completed v0.1 headless loop and v0.2 interactive TUI.

Broader roadmap items such as MCP, additional providers, sub-agents, VS Code integration, executable plugins, and sandboxing remain out of scope for this slice.

## Summary

The v0.3 release should make repeated project work smoother without making CodeGopher opaque.

Target user experience:

```bash
cgopher
cgopher -p "summarize what changed since the last release"
```

Inside the TUI, users should be able to:

- keep useful context across turns instead of starting each provider request from a blank conversation,
- see when context is compacted,
- save and inspect explicit memory,
- load plain Markdown skills,
- maintain visible session TODO state,
- continue using existing approvals, file safety, slash commands, shell passthrough, and session resume behavior.

Current implementation facts that v0.3 must account for:

- `run_agent` is one-shot and creates a fresh `Conversation` per turn.
- The TUI persists display messages, not provider-ready conversation context.
- `src/codegopher/memory` and `src/codegopher/skills` are placeholder packages.
- `.codegopherignore` traversal support already exists and should be reused.

## User-Facing Interfaces

Existing interfaces stay compatible:

- `cgopher`: launch the Textual TUI.
- `codegopher`: same behavior as `cgopher`.
- `cgopher -p/--prompt TEXT`: keep the headless one-shot behavior.
- Existing `--model`, `--provider`, `--base-url`, `--approval-mode`, `--debug`, and `--json` semantics remain intact.
- Existing TUI commands such as `/help`, `/clear`, `/model`, `/mode`, `/shell`, and `/stats` remain available.

New TUI command interface:

- `/compact [instructions]`: manually compact the current session context and record the summary as a visible session event.
- `/memory`: list session and project memories visible to the current session.
- `/forget ID`: delete a memory by id after confirmation or approval.
- `/skills`: list discovered skills and show which skills are currently loaded.
- `/todo`: show active TODO state.
- `/todo add TEXT`: add a user-visible TODO item.
- `/todo done ID`: mark a TODO item complete.

New model-facing tools:

- `save_memory`: approval-gated tool that stores explicit memory with `scope = "session" | "project"` and `content`.
- `update_todo`: tool that adds, updates, or completes session TODO items so multi-step work stays visible.

New local file conventions:

- Project skills: `.codegopher/skills/*/SKILL.md`.
- User skills: `~/.codegopher/skills/*/SKILL.md`.
- Built-in skills: packaged with CodeGopher under the Python package.

Skills are plain Markdown context only. v0.3 must not add executable plugins.

## Implementation Shape

### Session And Context Layer

Add a reusable session/context layer that can preserve provider-ready conversation state across TUI turns while preserving the existing headless `run_agent` behavior.

The session layer should own:

- conversation history used for provider messages,
- `ToolContext` and prior-read state,
- context budget metadata,
- compaction summaries,
- selected memories,
- loaded skills,
- session TODO state.

`run_agent` should remain import-compatible and behavior-compatible for headless one-shot use. The TUI should move toward the session layer so multiple turns can share provider-ready context.

### Context Budget And Compaction

Use the existing `tiktoken` dependency plus provider `context_window` when available.

Default policy:

- warn around 70 percent of the configured context window,
- compact around 80 percent before a turn would exceed the threshold,
- do not compact silently after the model has already lost important context.

Compaction should:

- summarize older conversation and relevant tool-result context,
- preserve recent turns verbatim,
- preserve active TODO state,
- preserve selected memory and loaded skill context,
- persist a visible compaction session entry with timestamp, reason, and summary.

Manual `/compact [instructions]` should use the same compaction pipeline, with optional user instructions included in the compaction prompt.

### Memory

Add local memory stores under CodeGopher data home, not in committed project files.

Memory scopes:

- Session memory keyed by session id.
- Project memory keyed by canonical cwd hash.

Memory entries should include:

- stable id,
- scope,
- content,
- created and updated timestamps,
- source metadata such as `user`, `tool`, or `system`,
- optional tags when useful.

Memory must not persist provider API keys, raw environment values, or hidden provider payloads.

The `save_memory` tool must be approval-gated and explicit. The model should not silently store memory without a visible tool call.

### Markdown Skills

Add skill discovery from project, user, and built-in locations.

A skill is an inspectable folder containing `SKILL.md`. v0.3 should load skill Markdown as context, not as executable code.

Skill loading should be progressive:

- explicit user mention or slash command should load a skill directly,
- simple metadata or keyword matching may suggest or load relevant skills,
- loaded skills should be visible in `/skills` and in session status or startup context.

Project skills should be easy to commit when the project chooses to do so. Local runtime data should remain ignored.

### Session TODO State

Add session TODO state for multi-step work.

TODO items should include:

- stable id,
- text,
- status such as `pending`, `in_progress`, or `done`,
- created and updated timestamps,
- optional source metadata.

The TUI should expose TODO state through `/todo`, `/todo add TEXT`, and `/todo done ID`.

The model-facing `update_todo` tool should update the same state so the user and model share one visible checklist. TODO state should be included in provider context when non-empty.

### Context Builder

Extend the context builder so provider messages include:

- current working directory,
- approval mode and tool safety rules,
- active TODO state,
- selected memories,
- compaction summaries,
- loaded skill Markdown,
- provider-ready conversation history.

The context builder should remain deterministic and testable. It should not mention unavailable future features.

## Safety And Scope

The v0.3 implementation must reuse existing safety behavior.

- Existing prior-read and parent-inspection checks remain authoritative.
- Existing project-root path boundaries remain authoritative.
- Approval mode semantics stay unchanged.
- Memory tools require approval unless approval policy explicitly permits them.
- Skills are read-only Markdown and do not execute code.
- `.codegopherignore` support continues to apply to traversal and search tools.
- Session data must not persist API keys or raw environment values.

Out of scope for v0.3:

- MCP client integration.
- Anthropic or Gemini providers.
- Sub-agent execution.
- VS Code extension work.
- Docker sandboxing.
- Executable plugin runtimes.
- Hosted or remote memory services.
- Full JSONL event stream mode.

## Testing Plan

Add tests incrementally with each milestone.

Expected test layers:

- Config schema tests for context, memory, skills, and TODO defaults.
- Unit tests for token accounting and compaction threshold behavior.
- Agent/session tests proving multi-turn context reaches the provider and one-shot `run_agent` still behaves as before.
- Context-builder tests for active TODO state, selected memory, compaction summaries, and loaded skills.
- Memory store CRUD tests for session and project scopes.
- Safety tests proving memory and session data do not persist secrets.
- Tool tests for approval-gated `save_memory` and `update_todo`.
- Skill discovery tests for project, user, and built-in locations.
- TUI tests for `/compact`, `/memory`, `/forget`, `/skills`, and `/todo`.
- Real OpenAI-compatible endpoint smoke test using local config kept outside git.

Final v0.3 verification:

```bash
source .venv/bin/activate
ruff check src/ tests/
mypy src/
python -m pytest
python -m hatch build
```
