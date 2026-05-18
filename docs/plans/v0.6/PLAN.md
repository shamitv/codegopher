# CodeGopher v0.6 Implementation Plan

This plan covers the v0.6 implementation slice: a native VS Code extension layer for CodeGopher. Existing terminal workflows remain the foundation. The extension should not replace `cgopher`, the Textual TUI, or the headless prompt mode; it should give developers an IDE-native way to use the same local agent.

Earlier roadmap items remain in place:

- v0.3: Context, Memory, And Skills.
- v0.4: OpenAI Responses API And MCP.
- v0.5: Repository Documentation And Static Security Skill Packs.
- v0.7: Advanced Coding Workflows.

## Summary

The v0.6 release should make CodeGopher usable from VS Code Chat:

```text
@codegopher explain this file
@codegopher fix the failing test
@codegopher review my current workspace changes
```

The VS Code extension will register a native chat participant named `@codegopher`. The extension will launch the local Python CLI as a subprocess and communicate with it through a newline-delimited JSON protocol. The Python agent remains authoritative for configuration loading, provider behavior, approvals, tool execution, prior-read enforcement, `.codegopherignore`, and workspace path safety.

The first IDE layer is intentionally not an LSP integration and not a webview app. It is a chat surface over the local CodeGopher agent.

## User-Facing Interfaces

Primary VS Code interface:

- `@codegopher`: native VS Code Chat participant.
- `@codegopher /help`: show extension-specific help and available commands.
- `@codegopher /status`: show CLI path, detected workspace root, active model/provider, approval mode, and subprocess state.
- `@codegopher /restart`: restart the CodeGopher subprocess after config or environment changes.

Extension commands:

- `CodeGopher: Open Chat`: focus VS Code Chat with `@codegopher`.
- `CodeGopher: Restart Agent`: stop and restart the subprocess.
- `CodeGopher: Show Protocol Trace`: open recent trace output when tracing is enabled.
- Internal approval commands used by chat buttons for approve and deny decisions.

Extension settings:

- `codegopher.cliPath`: path to the `cgopher` executable; default is `cgopher` on `PATH`.
- `codegopher.provider`: optional provider override passed to the CLI.
- `codegopher.model`: optional model override passed to the CLI.
- `codegopher.baseUrl`: optional OpenAI-compatible base URL override passed to the CLI.
- `codegopher.approvalMode`: optional `review`, `auto`, or `yolo` override.
- `codegopher.traceProtocol`: when true, write redacted protocol logs to the extension output channel.

Python CLI interfaces:

- `cgopher --events`: start a long-lived JSONL subprocess session over stdin/stdout.
- `cgopher --events -p "prompt"`: run one prompt and emit JSONL events until completion.
- Existing `cgopher`, `cgopher -p`, `--json`, `--debug`, provider overrides, and approval-mode behavior remain compatible.

## JSONL Protocol

Use protocol version `1`. Every JSON line must be a single object with:

- `version`: integer protocol version.
- `type`: event or command type.
- `session_id`: stable session identifier when known.
- `turn_id`: stable turn identifier for turn-scoped messages.

Commands from VS Code to Python:

- `start_turn`: prompt text, workspace root, optional selected file/editor metadata, and optional CLI override metadata.
- `approval_response`: pending approval id, approved boolean, and optional denial reason.
- `cancel_turn`: active turn id.
- `shutdown`: graceful subprocess stop.

Events from Python to VS Code:

- `session_started`: session id, cwd, provider, model, approval mode, and protocol version.
- `turn_started`: turn id and normalized cwd.
- `text_delta`: assistant answer text delta.
- `reasoning_delta`: reasoning delta; hidden by default in VS Code, counted for debug/progress.
- `tool_call`: tool id, tool name, and argument summary.
- `approval_request`: approval id, tool name, argument summary, and raw argument JSON when safe to display.
- `tool_result`: tool id, success/error state, and result summary.
- `error`: machine-readable code and user-facing message.
- `turn_complete`: final text, tool count, approval count, and iteration count.

Protocol constraints:

- stdout is reserved for JSONL protocol events in `--events` mode.
- human-readable diagnostics go to stderr or a trace file.
- malformed input receives a structured `error` event and does not crash the session unless recovery is impossible.
- secrets such as API keys and raw environment values must never be emitted in events or traces.

## Implementation Shape

Python runtime:

1. Add typed protocol models near the CLI or core boundary.
2. Add a reusable session runner that owns settings, provider, registry, conversation state, `ToolContext`, and callbacks.
3. Keep the existing one-shot `run_agent` API compatible.
4. Implement `--events` as a presentation layer over the session runner.
5. Support bidirectional approval by pausing the turn until an `approval_response` arrives.
6. Support cancellation by stopping the active turn, reporting a structured error, and returning the session to an idle state when possible.

VS Code extension:

1. Add `extensions/vscode` as a TypeScript package.
2. Register the `@codegopher` chat participant through the VS Code Chat Participant API.
3. Launch `cgopher --events` with the workspace root as cwd.
4. Parse JSONL stdout incrementally and route events to the active chat response stream.
5. Render assistant text as markdown, tool calls/results as progress or compact markdown, and approval requests as buttons.
6. Route approval button commands back to the pending subprocess request.
7. Respect cancellation tokens from VS Code Chat by sending `cancel_turn`.
8. Surface missing CLI, subprocess exits, malformed JSON, provider errors, and approval timeouts clearly.

Safety boundaries:

- The extension never executes file, shell, git, web, or MCP tools directly.
- Python safety checks remain authoritative.
- Approval mode semantics remain `review`, `auto`, and `yolo`.
- Workspace root selection must be explicit and visible in `/status`.
- Protocol tracing is opt-in and redacted.

Out of scope for v0.6:

- LSP diagnostics and code actions.
- A custom webview chat UI.
- A background daemon or HTTP server.
- Marketplace publishing automation beyond local VSIX packaging notes.
- Remote extension host support beyond documenting known limits.

## Testing Plan

Python tests:

- Protocol model encode/decode tests.
- CLI routing tests for `--events`, `--events -p`, and existing headless/TUI preservation.
- Event-stream tests for text, reasoning, tool calls, tool results, approvals, denial, provider errors, malformed input, and cancellation.
- Session runner tests proving `ToolContext` and prior-read behavior persist across turns.

VS Code extension tests:

- TypeScript unit tests for JSONL parsing, subprocess message routing, pending approval state, cancellation, and error mapping.
- VS Code integration tests using `@vscode/test-electron` for activation, chat participant registration, commands, and settings.
- Mock subprocess tests covering streaming, approval request/response, malformed JSON, subprocess crash, and restart.

Final v0.6 verification:

```bash
source .venv/bin/activate
ruff check src/ tests/
mypy src/
python -m pytest

cd extensions/vscode
npm run compile
npm run lint
npm test
```

Manual smoke checks:

- Open a workspace in VS Code and ask `@codegopher` a read-only question.
- Run a prompt that requests a tool call and confirm progress appears.
- Approve one tool call and deny another from VS Code Chat buttons.
- Cancel a long-running turn and confirm the subprocess returns to a usable state.
- Restart the agent from the command palette.
- Confirm `cgopher`, `cgopher -p`, and plain TUI startup still work outside VS Code.

## References

- VS Code Chat Participant API: https://code.visualstudio.com/api/extension-guides/ai/chat
- VS Code extension testing: https://code.visualstudio.com/api/working-with-extensions/testing-extension
