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

`npm test` launches a downloaded VS Code Insiders Extension Development Host through `@vscode/test-electron`. Using Insiders plus throwaway `.vscode-test` extension and user-data directories keeps automated tests isolated from a normal Stable VS Code session. If a shell is inherited from VS Code, the test runner clears `ELECTRON_RUN_AS_NODE` before launching the downloaded host.

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

After installation, open a disposable workspace and run `CodeGopher: Open Chat`, `@codegopher /status`, `CodeGopher: View LLM Endpoint`, and `CodeGopher: Manage MCP Servers`. If `cgopher` is not available on the VS Code process `PATH`, configure `codegopher.cliPath` to an absolute executable path before testing. Use `CodeGopher: Set API Key` to store the provider token in VS Code Secret Storage instead of relying on the Extension Development Host environment.

## Commands

The extension contributes these CodeGopher commands:

- `CodeGopher: Open Chat`
- `CodeGopher: Restart Agent`
- `CodeGopher: Set API Key`
- `CodeGopher: Clear API Key`
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
- `codegopher.apiKeyEnv`: optional environment variable name for the stored provider API key. Leave blank to expose a stored key as `OPENAI_API_KEY`; set it to values such as `HF_TOKEN` for Hugging Face Router.
- `codegopher.approvalMode`: optional `review`, `auto`, or `yolo` override.
- `codegopher.maxIterations`: per-turn agent loop limit passed as `--max-iterations`; defaults to `64`.
- `codegopher.traceProtocol`: enables redacted protocol trace logging when the events client exists.

For Hugging Face Router, configure `codegopher.baseUrl` as `https://router.huggingface.co/v1`, `codegopher.apiFamily` as `chat_completions`, `codegopher.model` with the routed model id, and `codegopher.apiKeyEnv` as `HF_TOKEN`. Then run `CodeGopher: Set API Key`, paste the Hugging Face token, and restart the agent.

## Events Boundary

The extension launches `cgopher --events` in the selected workspace root and communicates with it over JSONL. VS Code owns the UI surface for `@codegopher`, progress, approvals, cancellation, and command-palette interactions; Python owns provider selection, tool execution, config validation, MCP lifecycle, redaction, and workspace safety.
