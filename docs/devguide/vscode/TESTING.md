# VS Code Extension Testing

This guide describes how to test the planned CodeGopher VS Code integration across macOS, Windows, and Linux. The v0.6 extension package will live under `extensions/vscode`; commands in this guide assume that package exists and has installed npm dependencies.

The extension should be tested as a thin VS Code shell over the local Python engine. VS Code and TypeScript own UI, command routing, and subprocess lifecycle. Python remains authoritative for configuration, MCP validation, provider behavior, tool execution, approvals, redaction, and workspace safety.

## Test Layers

Use layered tests so failures are easy to isolate.

1. TypeScript unit tests
   - JSONL partial-line parsing.
   - Protocol event routing.
   - Pending turn and approval state.
   - CLI path resolution and restart lifecycle.
   - Configured LLM endpoint and MCP server command flows using mocked subprocess responses.

2. Mock subprocess tests
   - Simulate `cgopher --events` stdout, stderr, exit codes, malformed JSON, crashes, cancellation, and approval requests.
   - Verify TypeScript never executes tools or edits CodeGopher TOML directly.

3. VS Code integration tests
   - Run in an Extension Development Host with `@vscode/test-cli` and `@vscode/test-electron`.
   - Verify activation, contributed commands, settings, chat participant registration, command palette behavior, and subprocess error display.

4. Manual smoke tests
   - Launch an Extension Development Host.
   - Exercise `@codegopher /status`, a read-only prompt, approval buttons, cancellation, restart, LLM endpoint viewing, and MCP server management.

## Common Commands

From the extension package:

```bash
cd extensions/vscode
npm install
npm run compile
npm run lint
npm test
```

Recommended `.vscode-test.js` shape for automated integration tests:

```js
const { defineConfig } = require('@vscode/test-cli');

module.exports = defineConfig({
  files: 'out/test/**/*.test.js',
  workspaceFolder: './test-workspace',
  launchArgs: ['--disable-extensions']
});
```

The checked-in test runner targets a downloaded VS Code Insiders build with throwaway `.vscode-test` extension and user-data directories. This keeps automated tests isolated when Stable VS Code is already running as the developer's normal editor.

## macOS

Use VS Code Insiders for manual development if you want to keep Stable available for normal work.

Install the Insiders shell command from VS Code Insiders:

```text
Command Palette -> Shell Command: Install 'code-insiders' command in PATH
```

Open the repo in Insiders:

```bash
code-insiders /Users/username/path-to/codegopher
```

Manual Extension Development Host workflow:

1. Open the extension package in VS Code or VS Code Insiders.
2. Run `npm install` and `npm run compile`.
3. Press `F5` or run the extension launch configuration.
4. In the Extension Development Host, open a disposable workspace.
5. Run CodeGopher commands from the Command Palette and VS Code Chat.

CLI-driven extension tests cannot use a VS Code build that is already running. The default setup uses Stable for normal work and the downloaded Insiders build for automated tests. If you are also using Insiders for manual debugging, close all VS Code Insiders windows before running `npm test`.

macOS subprocess checks:

```bash
which cgopher
cgopher --help
code-insiders --version
```

If `cgopher` is only available inside a virtual environment, configure the extension test fixture to use an absolute `codegopher.cliPath` or launch VS Code from a shell where the virtual environment is active.

## Windows

Use PowerShell for repeatable local commands. Quote paths that contain spaces.

Install the VS Code or VS Code Insiders shell command if needed, then verify:

```powershell
code --version
code-insiders.cmd --version
where.exe cgopher
cgopher --help
```

Run extension checks:

```powershell
cd extensions\vscode
npm install
npm run compile
npm run lint
npm test
```

When testing `codegopher.cliPath`, include cases for:

- `cgopher` resolved from `PATH`.
- An absolute path such as `C:\Users\NAME\AppData\Local\Programs\Python\Python312\Scripts\cgopher.exe`.
- Paths containing spaces.
- Missing executable errors.

For manual testing, launch the Extension Development Host from VS Code or VS Code Insiders, open a disposable workspace, and run the same smoke checks as macOS. Keep environment-specific secrets out of settings committed to the repo; use `CodeGopher: Set API Key` for provider tokens and configure `codegopher.apiKeyEnv` only when the provider expects a non-default variable such as `HF_TOKEN`.

Example Hugging Face Router smoke settings:

```json
{
  "codegopher.cliPath": "D:\\work\\codegopher\\.venv\\Scripts\\cgopher.exe",
  "codegopher.baseUrl": "https://router.huggingface.co/v1",
  "codegopher.model": "Qwen/Qwen3.6-35B-A3B:featherless-ai",
  "codegopher.apiFamily": "chat_completions",
  "codegopher.apiKeyEnv": "HF_TOKEN"
}
```

After updating settings, run `CodeGopher: Set API Key`, paste the Hugging Face token, then run `CodeGopher: Restart Agent` or `@codegopher /restart`.

## Linux

Desktop Linux manual testing is similar to macOS:

```bash
code .
code-insiders .
which cgopher
cgopher --help
```

For headless CI, run VS Code extension tests under Xvfb:

```bash
cd extensions/vscode
npm install
npm run compile
npm run lint
xvfb-run -a npm test
```

Linux CI setup should ensure:

- Node.js and npm are installed.
- Python and CodeGopher test dependencies are installed.
- `cgopher` is on `PATH` or `codegopher.cliPath` points to an absolute executable path.
- Test workspaces are disposable.
- No real provider secrets are required for mock subprocess and command-registration tests.

If tests need a real local endpoint or MCP server, keep those as optional smoke checks and skip them clearly when dependencies are unavailable.

## Manual Smoke Checklist

Run these in an Extension Development Host with a disposable workspace:

- `CodeGopher: Open Chat` focuses VS Code Chat with `@codegopher`.
- `@codegopher /status` shows CLI path, workspace root, provider, model, approval mode, and subprocess state.
- A read-only prompt streams assistant text.
- The exact smoke prompt `@codegopher Reply with exactly: codegopher-smoke-ok` returns `codegopher-smoke-ok`.
- A tool-using prompt shows tool progress.
- Approve and deny buttons each send one approval response.
- Cancellation returns the subprocess to a usable state.
- `CodeGopher: Restart Agent` restarts the subprocess.
- `CodeGopher: View LLM Endpoint` shows provider, model, API family, base URL when present, and source metadata without secrets.
- `CodeGopher: Manage MCP Servers` can list, add, edit, disable, enable, and remove disposable MCP server config without exposing header or env values.

If chat stays on `Analyzing` and the CodeGopher Output channel stops after `Starting CodeGopher turn ...`, first verify the branch includes the long-lived events stdin fix and run `.\.venv\Scripts\python.exe -m pytest tests/integration/test_events_cli.py`. With `codegopher.traceProtocol` enabled, a healthy turn should show `start_turn`, `turn_started`, `text_delta`, and `turn_complete`.

## References

- VS Code extension testing: https://code.visualstudio.com/api/working-with-extensions/testing-extension
- VS Code continuous integration: https://code.visualstudio.com/api/working-with-extensions/continuous-integration
- VS Code command line: https://code.visualstudio.com/docs/editor/command-line
