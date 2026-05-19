# CodeGopher VS Code Extension

This package is the VS Code extension shell for CodeGopher. The v0.6 extension exposes the `@codegopher` chat participant and command-palette flows while the Python CLI remains authoritative for agent execution, configuration, MCP management, approvals, and filesystem safety.

The extension launches `cgopher --events` in the selected workspace root and communicates with it over newline-delimited JSON. VS Code owns chat rendering, command routing, progress, approvals, cancellation, restart, and user-facing error recovery; Python owns provider selection, tool execution, config validation, MCP lifecycle, redaction, and workspace safety.

## Local Development

Install dependencies and run the scaffold checks from this directory:

```sh
npm install
npm run compile
npm run lint
npm test
```

`npm test` launches a VS Code Extension Development Host through `@vscode/test-electron`. If a shell is inherited from VS Code, the test runner clears `ELECTRON_RUN_AS_NODE` before launching the downloaded host.

## Local VSIX Packaging

Build a local `.vsix` package from this directory:

```sh
npm install
npm run compile
npm run lint
npm test
npm run package
```

`npm run package` uses `@vscode/vsce` and writes a file such as `codegopher-vscode-0.0.1.vsix` in `extensions/vscode`. Treat the `.vsix` as a local release artifact; do not commit it.

Install the packaged extension into a local VS Code profile for smoke testing:

```sh
code --install-extension codegopher-vscode-0.0.1.vsix
```

For VS Code Insiders, use:

```sh
code-insiders --install-extension codegopher-vscode-0.0.1.vsix
```

After installation, open a disposable workspace and run `CodeGopher: Open Chat`, `@codegopher /status`, `CodeGopher: View LLM Endpoint`, and `CodeGopher: Manage MCP Servers`. If `cgopher` is not available on the VS Code process `PATH`, configure `codegopher.cliPath` to an absolute executable path before testing.

## Commands

The extension contributes these CodeGopher commands:

- `CodeGopher: Open Chat`
- `CodeGopher: Restart Agent`
- `CodeGopher: View LLM Endpoint`
- `CodeGopher: Manage MCP Servers`
- `CodeGopher: Show Protocol Trace`

The command handlers communicate with the Python events subprocess. They do not execute CodeGopher tools, parse CodeGopher TOML, or start MCP servers from TypeScript.

## Settings

The extension contributes these settings:

- `codegopher.cliPath`: path to the `cgopher` executable.
- `codegopher.provider`: optional provider override.
- `codegopher.model`: optional model override.
- `codegopher.baseUrl`: optional provider base URL override.
- `codegopher.apiFamily`: optional `chat_completions` or `responses` override.
- `codegopher.approvalMode`: optional `review`, `auto`, or `yolo` override.
- `codegopher.traceProtocol`: enables redacted protocol trace logging when the events client exists.

## Events Boundary

The extension launches `cgopher --events` in the selected workspace root and communicates with it over JSONL. VS Code owns the UI surface for `@codegopher`, progress, approvals, cancellation, and command-palette interactions; Python owns provider selection, tool execution, config validation, MCP lifecycle, redaction, and workspace safety.
