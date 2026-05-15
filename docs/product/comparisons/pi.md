# CodeGopher And Pi Product Comparison

Reviewed: 2026-05-15

This note captures product ideas CodeGopher can borrow from Pi, also called the Pi coding agent or Pi harness, without losing CodeGopher's own shape: a Python-native, local, auditable, approval-first terminal agent.

Pi's strongest product lesson is different from OpenCode's. OpenCode is a broad coding-agent product; Pi is a deliberately small harness that expects users, packages, and the agent itself to customize the workflow.

## Pi Signals Worth Tracking

Pi presents itself as a minimal terminal coding harness. Its public product surface emphasizes:

- A small core extended through TypeScript extensions, skills, prompt templates, themes, and Pi packages.
- Four default tools: read, write, edit, and bash, with optional read-only tools such as grep, find, and ls.
- A short system prompt that relies heavily on project context files.
- `AGENTS.md`, `CLAUDE.md`, `SYSTEM.md`, and append-system files for context engineering.
- Fuzzy `@` file references, path completion, pasted or dragged images, and shell-output prompt injection.
- Slash commands for login, model switching, session resume, session naming, tree navigation, compaction, export, sharing, and reload.
- Tree-structured JSONL sessions with branching, forking, cloning, naming, HTML export, and share links.
- Message steering while the agent is running: send an interruption-style message or queue a follow-up.
- Four integration modes: interactive TUI, print mode, JSON event stream mode, and RPC mode.
- Broad provider support through API keys, OAuth subscriptions, custom models, and custom providers.
- An explicit choice to omit built-in MCP, subagents, permission popups, plan mode, to-dos, and background bash from the core.

## Best Ideas To Borrow

### 1. Keep The Core Tool Surface Small

Pi's four-tool default is a useful forcing function. CodeGopher already has separate read, list, grep, glob, edit, write, and shell tools, which is fine for safety and tests. The product lesson is to keep the model-facing surface compact and predictable.

Good CodeGopher follow-ups:

- Keep tool descriptions short.
- Avoid adding convenience tools unless they reduce real user friction.
- Prefer a few sharp tools over a growing bag of overlapping operations.
- Consider a read-only tool profile for review/planning flows.

### 2. Treat Context Files As Product, Not Config Plumbing

Pi makes project instructions central with `AGENTS.md` and system prompt files. CodeGopher should do the same in a Python-native way:

- Load `AGENTS.md` when present.
- Support `.codegopher/PROJECT.md` or `.codegopher/SYSTEM.md` if CodeGopher-specific guidance is needed.
- Surface loaded context files in the TUI startup state.
- Add `/init` to generate a first project primer.
- Keep context files plain, committed, and easy to inspect.

This is a strong bridge between v0.2 session work and v0.3 memory/skills.

### 3. Tree-Structured Sessions

Pi's session model is more interesting than plain resume. A session can branch from earlier points, fork into a new session, clone the current branch, and export the result.

CodeGopher can start smaller:

- Save sessions as append-only JSONL.
- Give every message a stable ID and optional parent ID.
- Add `/resume`, `/new`, `/name`, and `/session` first.
- Leave `/tree`, `/fork`, and `/clone` as a v0.3 or v0.4 upgrade.

This makes later branching possible without redesigning the session format.

### 4. Message Steering While The Agent Runs

Pi lets the user send a steering message while the agent is working, then delivers it after the current tool call. This is a genuinely good terminal-agent UX idea.

CodeGopher could implement a simpler version:

- Let users queue one follow-up while a turn is running.
- Show queued input in the status area.
- Allow escape/cancel to pull the queued text back into the editor.
- Later distinguish "steer now" from "follow up after completion."

This belongs after v0.2's agent streaming and approvals are solid.

### 5. Prompt Templates As Lightweight Commands

Pi's prompt templates overlap with OpenCode custom commands, but the naming is useful: they are Markdown prompts first, commands second.

CodeGopher could support:

- `.codegopher/prompts/review.md` invoked as `/review`.
- Frontmatter for description and argument hints.
- `$ARGUMENTS` or template variables.
- `@file` mentions inside templates.

This is simpler and safer than a full plugin system.

### 6. Skills With Progressive Disclosure

Pi supports Agent Skills and loads them on demand. CodeGopher already has skills on the roadmap, so Pi reinforces the product direction:

- Skills should be inspectable folders with `SKILL.md`.
- The TUI should show which skills were discovered and which were loaded.
- Skills should load only when relevant.
- Project skills should be easy to commit.
- External skills should have an explicit trust story.

This is a better near-term extension model for CodeGopher than executable plugins.

### 7. JSON Event Stream Before A Server

Pi exposes JSON event stream and RPC modes. CodeGopher's current headless JSON output is useful, but a structured event stream would unlock integrations without a background server.

Potential shape:

- `cgopher --events -p "prompt"` emits JSONL events.
- Events include text deltas, reasoning deltas, tool calls, approvals, tool results, errors, and completion.
- Keep the schema close to the core agent callback/event types.
- Defer HTTP server or SDK work until there is clear demand.

This fits CodeGopher's "no server required" principle.

### 8. Compaction As A First-Class Session Event

Pi treats compaction and branch summarization as explicit session mechanics. CodeGopher has context-window tracking and compaction planned for v0.3; the product lesson is to make compaction visible:

- Record compaction entries in the session.
- Show when compaction happened and why.
- Let users manually trigger compaction with optional instructions.
- Keep summaries inspectable.

The user should never wonder why old context disappeared.

### 9. Model Switching With Context Handoff

Pi emphasizes broad provider support and mid-session model switching. CodeGopher does not need a giant provider catalog immediately, but it should design for handoff:

- Store provider/model metadata per turn.
- Preserve provider capability flags.
- Keep reasoning content separate from final answer text.
- Be explicit when a resumed session changes model/provider.

This supports v0.2 thinking rendering and v0.4 provider work.

### 10. Extensibility Vocabulary

Pi has a clear vocabulary:

- Prompt templates for reusable prompts.
- Skills for reusable capabilities.
- Extensions for executable behavior.
- Packages for distribution.

CodeGopher should adopt a similarly crisp vocabulary, even if the implementation differs:

- Commands or prompt templates for reusable prompts.
- Skills for model-readable procedures and helper assets.
- Tools for trusted Python-side actions.
- Plugins only later, if executable extension points become necessary.

## Ideas To Treat Carefully

### YOLO By Default

Pi intentionally runs without built-in permission prompts. CodeGopher should not copy this. CodeGopher's differentiator is approval-first local work, prior-read enforcement, and visible risky actions.

The useful lesson is not "remove safety." It is:

- Keep safety honest and understandable.
- Avoid pretending approval prompts solve all prompt-injection risks.
- Make container/sandbox guidance explicit for high-risk work.
- Let advanced users choose `yolo`, but never make it the default.

### Executable Extension Runtime

Pi's TypeScript extension layer is powerful, but CodeGopher should not rush into a Python plugin runtime. Executable extensions are a trust, compatibility, and support burden.

Better sequence:

1. Prompt templates.
2. Markdown skills.
3. Project-level trusted Python tools, if needed.
4. Plugin/package runtime much later.

### No Plan Mode

Pi intentionally omits built-in plan mode and suggests files or tool allowlists instead. CodeGopher should not copy the omission outright. A visible Plan/Build distinction still fits CodeGopher's approval-first product.

The borrowable part is file-backed planning:

- Plans should be written to project files when they matter.
- Plans should be editable by the user.
- Plans should survive session boundaries.

### No MCP In Core

Pi argues that MCP can be context-heavy and better represented by CLI wrappers in many cases. CodeGopher already has MCP on the roadmap, but this is a useful caution:

- Do not make MCP a required part of the core loop.
- Lazy-load MCP tools after explicit configuration.
- Show tool count and context impact.
- Prefer narrow tools over broad tool dumps.

### No Background Bash

Pi pushes users toward tmux for long-running processes. CodeGopher should be cautious here. Background process management is useful, but it can easily become unreliable.

For now:

- Keep v0.2 shell passthrough foreground and approval-gated.
- Record stdout, stderr, exit code, and timeout clearly.
- Consider tmux guidance before implementing background process management.

## Ideas To Avoid For Now

These Pi areas are useful, but probably not near-term priorities for CodeGopher:

- TypeScript extension runtime.
- Package manager for executable extensions.
- Hosted or gist-backed sharing.
- Custom TUI component API.
- OAuth subscription login flows.
- Browser or Slack embedding.
- Full RPC protocol before the core event schema settles.
- Making unrestricted execution the default.

## Suggested Roadmap Impact

Near-term:

- Make v0.2 `@` mentions feel like a real input primitive.
- Design v0.2 session persistence as append-only JSONL with stable message IDs.
- Add session naming and local HTML/Markdown export if scope allows.
- Keep shell passthrough foreground, explicit, and inspectable.

Medium-term:

- Add `/init` for project context files.
- Add prompt templates before any executable plugin system.
- Add Markdown skills with progressive disclosure.
- Add manual and automatic compaction entries.
- Add a JSONL event stream mode before an HTTP server.

Longer-term:

- Consider branchable session trees.
- Add file-backed planning as part of Plan/Build mode.
- Add trusted project tools carefully.
- Revisit MCP only with lazy loading and visible context cost.

## Sources

- Pi homepage: https://pi.dev/
- Pi docs overview: https://pi.dev/docs/latest
- Pi usage docs: https://pi.dev/docs/latest/usage
- Pi providers docs: https://pi.dev/docs/latest/providers
- Pi sessions docs: https://pi.dev/docs/latest/sessions
- Pi compaction docs: https://pi.dev/docs/latest/compaction
- Pi extensions docs: https://pi.dev/docs/latest/extensions
- Pi skills docs: https://pi.dev/docs/latest/skills
- Pi prompt templates docs: https://pi.dev/docs/latest/prompt-templates
- Pi packages docs: https://pi.dev/docs/latest/packages
- Pi RPC docs: https://pi.dev/docs/latest/rpc
- Pi JSON event stream docs: https://pi.dev/docs/latest/json
- Mario Zechner's Pi design post: https://mariozechner.at/posts/2025-11-30-pi-coding-agent/
