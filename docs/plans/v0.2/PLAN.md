# CodeGopher v0.2 Implementation Plan

This plan covers the v0.2 implementation slice: an interactive terminal experience built on top of the completed v0.1 headless agent loop. Broader roadmap items such as memory, skills, MCP, additional providers, sub-agents, and sandboxing remain out of scope unless they are explicitly needed for the terminal shell.

## Summary

The v0.2 release should make plain `cgopher` useful without requiring `-p/--prompt`.

Target user experience:

```bash
cgopher
cgopher -p "explain this project"
```

Plain `cgopher` launches an interactive terminal session. Existing headless behavior stays intact: `cgopher -p "prompt"` runs one prompt and exits, including `--json`, `--debug`, provider overrides, and approval-mode flags.

If no prompt is provided in a non-TTY context, the CLI should fail clearly and tell the user to pass `-p/--prompt`.

## User-Facing Interfaces

Primary interfaces:

- `cgopher`: launch the Textual TUI.
- `codegopher`: same behavior as `cgopher`.
- `cgopher -p/--prompt TEXT`: keep v0.1 headless behavior.
- `--model`, `--provider`, `--base-url`, `--approval-mode`, `--debug`, and `--json`: preserve existing headless behavior; options that affect runtime settings should also initialize the TUI session when applicable.

TUI-only command interface:

- `/help`: show available slash commands.
- `/clear`: clear visible chat history for the current session.
- `/model`: show or update the active model.
- `/mode`: show or update the approval mode.
- `/stats`: show session counters such as turns, tool calls, approvals, and elapsed time.

File and shell interfaces:

- `@path` mentions expand file content into the submitted prompt using existing read safety rules.
- `@glob` mentions expand bounded sets of files using existing glob/read-many behavior and `.codegopherignore`.
- Shell passthrough must require explicit approval before execution, even when typed directly in the TUI.

Thinking-content interface:

- Provider `reasoning_content` should be represented separately from final answer text.
- TUI displays thinking content collapsed by default.
- Headless `--debug` may show thinking content in a visibly distinct form.
- Headless `--json` final text must exclude thinking content.

## Implementation Shape

Use Textual as the primary UI stack.

Add a TUI package that stays separate from the headless Click entry point and the core agent loop. The CLI should route to either headless mode or TUI mode:

1. Load settings once through the existing config loader.
2. If `--prompt` is present, run the current headless path.
3. If `--prompt` is absent and stdin/stdout support an interactive terminal, launch the TUI.
4. If `--prompt` is absent and the process is non-interactive, return a clear Click error.

The TUI should initially be thin over the existing runtime:

- The app owns session state, visible chat history, command input, status, approval prompts, and session counters.
- The core agent loop remains presentation-agnostic.
- The agent loop should expose stream callbacks or an async event interface so the TUI can render text deltas, reasoning deltas, tool-call requests, approval decisions, tool results, and final completion without duplicating agent orchestration.
- Approval decisions should continue to use `review`, `auto`, and `yolo`, but the TUI supplies the interactive approval UI instead of the headless prompt helper.

Session persistence should be local and transparent:

- Store resumable session files under a project/user CodeGopher data location.
- Persist user turns, assistant turns, tool call summaries, final tool results, runtime settings, and enough metadata to resume safely.
- Do not persist provider API keys.
- Keep the first implementation simple and text-based; richer memory belongs to v0.3.

## Safety And Scope

The v0.2 TUI must reuse v0.1 safety behavior.

- Existing prior-read and parent-inspection checks remain authoritative.
- Existing project-root path boundaries remain authoritative.
- Approval mode semantics stay unchanged.
- Shell passthrough and risky tool calls require approval unless `yolo` is active.
- Slash commands must not bypass tool approval or filesystem safety checks.

Out of scope for v0.2:

- Persistent semantic memory.
- Skill discovery.
- MCP client integration.
- Anthropic or Gemini providers.
- Sub-agent execution.
- Docker sandboxing.
- Web fetch/search tools.

## Testing Plan

Add tests incrementally with each milestone.

Expected test layers:

- CLI routing tests for headless preservation, TUI launch, and non-TTY errors.
- Textual app tests using Textual's test harness for layout, input submission, slash commands, and approval UI.
- Unit tests for file mention parsing and expansion.
- Agent-loop callback/event tests using `MockProvider`.
- Session persistence tests using temporary directories.
- Provider parsing tests for reasoning-content events.
- Full-suite checks before marking v0.2 complete.

Final v0.2 verification:

```bash
source .venv/bin/activate
ruff check src/ tests/
mypy src/
python -m pytest
python -m hatch build
```
