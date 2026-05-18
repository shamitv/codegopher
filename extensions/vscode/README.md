# CodeGopher VS Code Extension

This package is the VS Code extension shell for CodeGopher. The v0.6 extension will expose the `@codegopher` chat participant and command-palette flows while the Python CLI remains authoritative for agent execution, configuration, MCP management, approvals, and filesystem safety.

Milestone 5 only contains the scaffold: metadata, settings, placeholder commands, TypeScript tooling, and extension-host activation tests. Later milestones wire the extension to `cgopher --events` over newline-delimited JSON.

## Local Development

Install dependencies and run the scaffold checks from this directory:

```sh
npm install
npm run compile
npm run lint
npm test
```

`npm test` launches a VS Code Extension Development Host through `@vscode/test-electron`. If a shell is inherited from VS Code, the test runner clears `ELECTRON_RUN_AS_NODE` before launching the downloaded host.

## Commands

The scaffold contributes these CodeGopher commands:

- `CodeGopher: Open Chat`
- `CodeGopher: Restart Agent`
- `CodeGopher: View LLM Endpoint`
- `CodeGopher: Manage MCP Servers`
- `CodeGopher: Show Protocol Trace`

The command handlers are intentionally lightweight placeholders until the TypeScript events client is added. They do not execute CodeGopher tools, parse CodeGopher TOML, or start MCP servers from TypeScript.

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

Future milestones launch `cgopher --events` in the selected workspace root and communicate with it over JSONL. VS Code owns the UI surface for `@codegopher`, progress, approvals, cancellation, and command-palette interactions; Python owns provider selection, tool execution, config validation, MCP lifecycle, redaction, and workspace safety.
