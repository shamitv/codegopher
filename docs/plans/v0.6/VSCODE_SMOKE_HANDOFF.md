# VS Code Manual Smoke Test Handoff

Date: 2026-05-19

Branch: `impl/v0.6-vscode-extension`

## Purpose

This handoff is for the developer picking up the remaining Milestone 11 manual VS Code smoke gates:

- T086: Run a manual VS Code Chat smoke test with `@codegopher`.
- T087: Run manual configured LLM endpoint and MCP server management smoke tests in VS Code.

Do not check or commit T086/T087 until the manual Extension Development Host workflows pass.

## Current State

Automated release readiness is complete through T085. The remaining work is manual validation in a VS Code Extension Development Host.

Recent commits relevant to this handoff:

- `2abae2d Add VS Code API key secret configuration`
  - Adds `CodeGopher: Set API Key` and `CodeGopher: Clear API Key`.
  - Stores provider tokens in VS Code Secret Storage.
  - Adds `codegopher.apiKeyEnv` so a stored token can be exposed to `cgopher` as `HF_TOKEN`, `OPENAI_API_KEY`, or another provider-specific env var.
- `b4bd4db Refresh VS Code client on restart`
  - Fixes a stale-client restart issue where `/restart` could reuse old settings and continue expecting `OPENAI_API_KEY`.
- `6afc1cc Fix long-lived events stdin blocking`
  - Fixes the long-lived `cgopher --events` command loop so it can run a `start_turn` while waiting for future stdin commands from VS Code.
  - Adds a regression test proving `turn_complete` arrives without requiring an additional stdin line.

Latest extension verification after the VS Code extension commits:

```powershell
cd D:\work\codegopher\extensions\vscode
npm run compile
npm run lint
npm test
```

Result: `107 passing`.

The VS Code test runner may still print an Insiders mutex diagnostic after the test run, but the command exited successfully during the last verification.

Latest Python verification after the long-lived events fix:

```powershell
.\.venv\Scripts\python.exe -m ruff check src/codegopher/events/cli.py tests/integration/test_events_cli.py
.\.venv\Scripts\python.exe -m pytest tests/integration/test_events_cli.py
.\.venv\Scripts\python.exe -m pytest
```

Result: `584 passed, 1 skipped`.

## Important UX Rule

Do not put the Hugging Face token value in VS Code settings.

Use settings only for non-secret configuration:

```json
{
  "codegopher.cliPath": "D:\\work\\codegopher\\.venv\\Scripts\\cgopher.exe",
  "codegopher.baseUrl": "https://router.huggingface.co/v1",
  "codegopher.model": "Qwen/Qwen3.6-35B-A3B:featherless-ai",
  "codegopher.apiFamily": "chat_completions",
  "codegopher.apiKeyEnv": "HF_TOKEN",
  "codegopher.maxIterations": 64
}
```

Then run `CodeGopher: Set API Key` in the Extension Development Host and paste the actual Hugging Face token into the password prompt. The extension should inject:

```text
CODEGOPHER_API_KEY_ENV=HF_TOKEN
HF_TOKEN=<stored VS Code secret>
```

The token itself must never be committed, pasted into docs, or stored in `settings.json`.

## Known In-Progress Symptom

During the current manual attempt, `@codegopher /restart` still reported:

```text
Missing API key: expected environment variable OPENAI_API_KEY
```

With the settings above and the latest compiled extension code, a fresh Extension Development Host should no longer fall back to `OPENAI_API_KEY`. If it still does, the host is probably running an old extension instance, using a stale client, or not reading the expected user/workspace settings.

The first diagnostic check is:

```text
@codegopher /status
```

Expected status line:

```text
API key env: HF_TOKEN
Max iterations: 64
```

If `/status` does not show `HF_TOKEN`, do not continue the smoke test. Fix the Extension Development Host/settings issue first.

## Resolved Stuck Turn Symptom

The manual smoke attempt also exposed a separate hang:

```text
Starting CodeGopher turn ...
```

The VS Code Output channel stopped there, even though one-shot CLI calls such as `cgopher -p "Reply with exactly: codegopher-smoke-ok"` returned correctly. Root cause: the Python long-lived events command loop created a turn task and then blocked synchronously waiting for the next stdin line, preventing the asyncio turn task from running.

Commit `6afc1cc` fixes this by reading stdin through `asyncio.to_thread(...)` and keeping the event loop free to run the active turn. After this fix, the Extension Development Host successfully returned:

```text
codegopher-smoke-ok
```

The trace output showed `start_turn`, `turn_started`, `text_delta`, and `turn_complete` events for the smoke prompt.

## Fresh Manual Test Procedure

Use VS Code Insiders for this test so the normal Stable VS Code session does not collide with the extension test/debug host.

1. In the outer VS Code window, open `D:\work\codegopher\extensions\vscode`.
2. Run:

   ```powershell
   npm run compile
   ```

3. Stop any existing extension debug session with the red Stop button.
4. Close any existing Extension Development Host windows.
5. Press `F5` from the outer VS Code window.
6. In the new Extension Development Host, open the disposable workspace:

   ```text
   D:\work\secure-code-hunt\apps\java\app-06-hr-management
   ```

7. In the Extension Development Host settings, set the CodeGopher settings from the JSON block above.
8. Run `Developer: Reload Window` inside the Extension Development Host.
9. Run `CodeGopher: Set API Key` and paste the Hugging Face token.
10. Start a fresh VS Code Chat session.
11. Run:

    ```text
    @codegopher /status
    ```

12. Confirm the status includes:

    ```text
    API key env: HF_TOKEN
    Max iterations: 64
    ```

13. Run:

    ```text
    @codegopher /restart
    ```

14. Run:

    ```text
    @codegopher Reply with exactly: codegopher-smoke-ok
    ```

15. Confirm the response is exactly:

    ```text
    codegopher-smoke-ok
    ```

The model picker in the VS Code Chat input is not used by CodeGopher. The effective model for CodeGopher comes from `codegopher.model`.

## T086 Checklist

Mark T086 complete only after these pass in the Extension Development Host:

- `CodeGopher: Open Chat` opens/focuses VS Code Chat with `@codegopher`.
- `@codegopher /status` shows the expected CLI path, workspace root, provider/model, approval mode, `API key env: HF_TOKEN`, and `Max iterations: 64`.
- `@codegopher /restart` succeeds without `OPENAI_API_KEY` or `HF_TOKEN` missing-key errors.
- A simple read-only prompt returns a model response.
- The exact smoke prompt returns `codegopher-smoke-ok`.
- A tool-using prompt shows tool progress and approval UX as expected.
- Cancellation leaves the subprocess usable for another prompt.

After T086 passes:

1. Check T086 in `docs/plans/v0.6/TODO.md`.
2. Commit only that confirmation, for example:

   ```powershell
   git add docs/plans/v0.6/TODO.md
   git commit -m "T086 Confirm VS Code chat smoke test"
   ```

## T087 Checklist

Mark T087 complete only after these pass in the Extension Development Host:

- `CodeGopher: View LLM Endpoint` shows the configured HF Router endpoint without secrets.
- The endpoint view shows:
  - model: `Qwen/Qwen3.6-35B-A3B:featherless-ai`
  - API family: `chat_completions`
  - base URL: `https://router.huggingface.co/v1`
- `CodeGopher: Manage MCP Servers` can list disposable project config.
- Add/edit/disable/enable/remove flows work for disposable MCP server config.
- No API keys, raw env values, or MCP header secrets appear in UI or output channel logs.

After T087 passes:

1. Check T087 in `docs/plans/v0.6/TODO.md`.
2. Commit only that confirmation, for example:

   ```powershell
   git add docs/plans/v0.6/TODO.md
   git commit -m "T087 Confirm VS Code endpoint and MCP smoke tests"
   ```

## Troubleshooting

If the error still says `OPENAI_API_KEY`:

- Run `@codegopher /status` and check whether `API key env` is `HF_TOKEN`.
- Confirm the Extension Development Host is running code compiled after `b4bd4db`.
- Stop the debug session, close the host, run `npm run compile`, and launch a new host with `F5`.
- Run `Developer: Reload Window` in the Extension Development Host.
- Run `CodeGopher: Set API Key` again. Secret Storage is per extension host/user-data context, so a new host may require re-entering the token.
- Confirm the settings are in the Extension Development Host, not only the outer VS Code window.

If the error says `HF_TOKEN` is missing:

- The latest code/settings are being read, but the secret is not stored in that host context.
- Run `CodeGopher: Set API Key` again and restart the agent.

If `cgopher` is not found:

- Set `codegopher.cliPath` to the absolute venv executable:

  ```text
  D:\work\codegopher\.venv\Scripts\cgopher.exe
  ```

If the CLI path works in a terminal but not in the extension:

- Remember that Extension Development Host subprocesses do not necessarily inherit the same activated virtualenv environment as an integrated terminal.
- Prefer the absolute `codegopher.cliPath` during manual smoke testing.

If VS Code gets stuck at `Starting CodeGopher turn ...`:

- Confirm the branch includes `6afc1cc Fix long-lived events stdin blocking`.
- Re-run `.\.venv\Scripts\python.exe -m pytest tests/integration/test_events_cli.py`.
- Stop and relaunch the Extension Development Host so it uses the updated Python source.
- Enable `codegopher.traceProtocol`, rerun the smoke prompt, and confirm `start_turn`, `turn_started`, `text_delta`, and `turn_complete` appear in the CodeGopher Output channel.

If a larger audit/report prompt fails with `Agent exceeded max iterations`:

- Confirm the branch includes the `--max-iterations` / `codegopher.maxIterations` change.
- Keep `codegopher.maxIterations` at the default `64` for manual smoke testing unless a smaller cap is intentionally under test.
- If the trace shows a blocked write such as `list_dir must inspect parent directory docs/audit first`, ask CodeGopher to list the exact parent directory before retrying the write.

## Files To Reference

- `docs/devguide/vscode/TESTING.md`
- `docs/plans/v0.6/TODO.md`
- `docs/plans/v0.6/STATUS.md`
- `extensions/vscode/README.md`
- `extensions/vscode/package.json`
- `extensions/vscode/src/extension.ts`
- `extensions/vscode/src/chat.ts`
- `extensions/vscode/src/client.ts`
- `src/codegopher/events/cli.py`
- `tests/integration/test_events_cli.py`
