import * as vscode from "vscode";

import type { CodeGopherConfigClient } from "./client";
import type { ConfigSnapshotEvent, McpServerPayload, McpServerSnapshotPayload, McpServersEvent } from "./protocol";

export interface CodeGopherConfigUiControllerOptions {
  clientProvider: () => CodeGopherConfigClient;
  dialogs?: CodeGopherConfigDialogs;
}

export interface CodeGopherConfigDialogs {
  showInformationMessage(message: string, ...items: string[]): PromiseLike<string | undefined>;
  showErrorMessage(message: string, ...items: string[]): PromiseLike<string | undefined>;
  showQuickPick<T extends CodeGopherQuickPickItem>(
    items: readonly T[],
    options?: CodeGopherQuickPickOptions
  ): PromiseLike<T | undefined>;
  showInputBox(options?: CodeGopherInputBoxOptions): PromiseLike<string | undefined>;
}

export interface CodeGopherQuickPickItem {
  label: string;
  description?: string;
  detail?: string;
}

export interface CodeGopherQuickPickOptions {
  title?: string;
  placeHolder?: string;
}

export interface CodeGopherInputBoxOptions {
  title?: string;
  prompt?: string;
  placeHolder?: string;
  value?: string;
  ignoreFocusOut?: boolean;
}

export interface McpServerListItem extends CodeGopherQuickPickItem {
  itemType: "add_stdio" | "add_sse" | "server";
  serverName?: string;
  server?: McpServerSnapshotPayload;
}

export class CodeGopherConfigUiController {
  private readonly clientProvider: () => CodeGopherConfigClient;
  private readonly dialogs: CodeGopherConfigDialogs;

  constructor(options: CodeGopherConfigUiControllerOptions) {
    this.clientProvider = options.clientProvider;
    this.dialogs = options.dialogs ?? defaultDialogs();
  }

  async viewLlmEndpoint(): Promise<void> {
    try {
      const snapshot = await this.clientProvider().getEffectiveConfig();
      await this.dialogs.showInformationMessage(formatEndpointDetails(snapshot));
    } catch (error) {
      await this.dialogs.showErrorMessage(`CodeGopher endpoint inspection failed: ${errorMessage(error)}`);
    }
  }

  async manageMcpServers(): Promise<void> {
    try {
      const snapshot = await this.clientProvider().listMcpServers();
      const picked = await this.dialogs.showQuickPick(formatMcpServerListItems(snapshot), {
        title: "CodeGopher MCP Servers",
        placeHolder: "Select a configured MCP server or add a new one"
      });
      if (!picked) {
        return;
      }
      if (picked.itemType === "add_stdio") {
        await this.createStdioServer();
      }
      if (picked.itemType === "add_sse") {
        await this.createSseServer();
      }
    } catch (error) {
      await this.dialogs.showErrorMessage(`CodeGopher MCP server management failed: ${errorMessage(error)}`);
    }
  }

  private async createStdioServer(): Promise<void> {
    const serverName = await this.promptServerName("Add stdio MCP server");
    if (!serverName) {
      return;
    }
    const command = await this.promptRequiredText("Command", "Command used to launch the MCP server", "npx");
    if (!command) {
      return;
    }
    const argsText = await this.dialogs.showInputBox({
      title: "Arguments",
      prompt: "JSON string array of command arguments",
      placeHolder: "[\"@modelcontextprotocol/server-filesystem\", \".\"]",
      value: "[]",
      ignoreFocusOut: true
    });
    if (argsText === undefined) {
      return;
    }
    const args = parseJsonStringArray(argsText, "Arguments");
    const cwd = await this.dialogs.showInputBox({
      title: "Working directory",
      prompt: "Optional working directory for the MCP server",
      placeHolder: "/absolute/path or blank",
      ignoreFocusOut: true
    });
    if (cwd === undefined) {
      return;
    }
    const startupTimeoutText = await this.dialogs.showInputBox({
      title: "Startup timeout",
      prompt: "Optional positive startup timeout in seconds",
      placeHolder: "30",
      ignoreFocusOut: true
    });
    if (startupTimeoutText === undefined) {
      return;
    }
    const startupTimeout = parseOptionalPositiveNumber(startupTimeoutText, "Startup timeout");
    const server: McpServerPayload = {
      enabled: true,
      transport: "stdio",
      command,
      args
    };
    if (cwd.trim()) {
      server.cwd = cwd.trim();
    }
    if (startupTimeout !== undefined) {
      server.startup_timeout_seconds = startupTimeout;
    }

    await this.clientProvider().saveMcpServer(serverName, server);
    await this.dialogs.showInformationMessage(`CodeGopher MCP server saved: ${serverName}`);
  }

  private async createSseServer(): Promise<void> {
    const serverName = await this.promptServerName("Add SSE MCP server");
    if (!serverName) {
      return;
    }
    const url = await this.promptRequiredText("URL", "SSE URL for the MCP server", "https://example.test/sse");
    if (!url) {
      return;
    }
    const timeoutText = await this.dialogs.showInputBox({
      title: "Request timeout",
      prompt: "Optional positive request timeout in seconds",
      placeHolder: "5",
      ignoreFocusOut: true
    });
    if (timeoutText === undefined) {
      return;
    }
    const readTimeoutText = await this.dialogs.showInputBox({
      title: "SSE read timeout",
      prompt: "Optional positive SSE read timeout in seconds",
      placeHolder: "300",
      ignoreFocusOut: true
    });
    if (readTimeoutText === undefined) {
      return;
    }
    const timeout = parseOptionalPositiveNumber(timeoutText, "Request timeout");
    const readTimeout = parseOptionalPositiveNumber(readTimeoutText, "SSE read timeout");
    const server: McpServerPayload = {
      enabled: true,
      transport: "sse",
      url
    };
    if (timeout !== undefined) {
      server.timeout_seconds = timeout;
    }
    if (readTimeout !== undefined) {
      server.sse_read_timeout_seconds = readTimeout;
    }

    await this.clientProvider().saveMcpServer(serverName, server);
    await this.dialogs.showInformationMessage(`CodeGopher MCP server saved: ${serverName}`);
  }

  private async promptServerName(title: string): Promise<string | undefined> {
    const value = await this.dialogs.showInputBox({
      title,
      prompt: "MCP server name",
      placeHolder: "letters, numbers, '_' and '-'",
      ignoreFocusOut: true
    });
    if (value === undefined) {
      return undefined;
    }
    const serverName = value.trim();
    const validationError = validateMcpServerName(serverName);
    if (validationError) {
      await this.dialogs.showErrorMessage(validationError);
      return undefined;
    }
    return serverName;
  }

  private async promptRequiredText(
    title: string,
    prompt: string,
    placeHolder: string
  ): Promise<string | undefined> {
    const value = await this.dialogs.showInputBox({
      title,
      prompt,
      placeHolder,
      ignoreFocusOut: true
    });
    if (value === undefined) {
      return undefined;
    }
    const trimmed = value.trim();
    if (!trimmed) {
      await this.dialogs.showErrorMessage(`${title} is required.`);
      return undefined;
    }
    return trimmed;
  }
}

export function formatEndpointDetails(snapshot: ConfigSnapshotEvent): string {
  return [
    "CodeGopher LLM Endpoint",
    `Workspace: ${redactDisplayText(snapshot.workspace_root)}`,
    `Provider: ${redactDisplayText(snapshot.provider)}`,
    `Model: ${redactDisplayText(snapshot.model)}`,
    `API family: ${redactDisplayText(snapshot.api_family)}`,
    `Base URL: ${redactDisplayText(snapshot.base_url ?? "Not configured")}`,
    `Config sources: ${formatConfigSources(snapshot.config_sources)}`
  ].join("\n");
}

function defaultDialogs(): CodeGopherConfigDialogs {
  return {
    showInformationMessage: (message, ...items) => vscode.window.showInformationMessage(message, ...items),
    showErrorMessage: (message, ...items) => vscode.window.showErrorMessage(message, ...items),
    showQuickPick: (items, options) => vscode.window.showQuickPick(items, options),
    showInputBox: (options) => vscode.window.showInputBox(options)
  };
}

function errorMessage(error: unknown): string {
  if (error instanceof Error && error.message) {
    return error.message;
  }
  return "CodeGopher request failed.";
}

function formatConfigSources(sources: string[] | undefined): string {
  if (!sources || sources.length === 0) {
    return "Not reported";
  }
  return sources.map((source) => redactDisplayText(source)).join(", ");
}

export function redactDisplayText(value: string): string {
  return value
    .replace(/(authorization\s*=\s*)(?:bearer\s+)?[^&\s]+/gi, "$1[redacted]")
    .replace(/(api[_-]?key|authorization|password|passwd|secret|token|credential)=([^&\s]+)/gi, "$1=[redacted]")
    .replace(/(bearer\s+)[^\s,;]+/gi, "$1[redacted]")
    .replace(/\/\/[^/@\s]+@/g, "//[redacted]@");
}

export function validateMcpServerName(serverName: string): string | undefined {
  if (!/^[A-Za-z0-9_-]+$/.test(serverName)) {
    return "MCP server names may contain only letters, numbers, '_' and '-'.";
  }
  return undefined;
}

export function parseJsonStringArray(value: string, fieldName: string): string[] {
  const trimmed = value.trim();
  if (!trimmed) {
    return [];
  }
  let parsed: unknown;
  try {
    parsed = JSON.parse(trimmed);
  } catch (error) {
    const detail = error instanceof Error ? error.message : "invalid JSON";
    throw new Error(`${fieldName} must be a JSON string array: ${detail}`, { cause: error });
  }
  if (!Array.isArray(parsed) || parsed.some((item) => typeof item !== "string")) {
    throw new Error(`${fieldName} must be a JSON string array.`);
  }
  return parsed;
}

export function parseOptionalPositiveNumber(value: string, fieldName: string): number | undefined {
  const trimmed = value.trim();
  if (!trimmed) {
    return undefined;
  }
  const parsed = Number(trimmed);
  if (!Number.isFinite(parsed) || parsed <= 0) {
    throw new Error(`${fieldName} must be a positive number.`);
  }
  return parsed;
}

export function formatMcpServerListItems(snapshot: McpServersEvent): McpServerListItem[] {
  return [
    {
      itemType: "add_stdio",
      label: "$(add) Add stdio server",
      description: "project",
      detail: "Create a project-local MCP server launched with a command"
    },
    {
      itemType: "add_sse",
      label: "$(add) Add SSE server",
      description: "project",
      detail: "Create a project-local MCP server connected by URL"
    },
    ...(snapshot.servers ?? []).map(formatMcpServerListItem)
  ];
}

function formatMcpServerListItem(snapshot: McpServerSnapshotPayload): McpServerListItem {
  const transport = snapshot.server.transport ?? "stdio";
  const enabled = snapshot.server.enabled === false ? "disabled" : "enabled";
  const source = snapshot.source ?? "unknown source";
  return {
    itemType: "server",
    serverName: snapshot.name,
    server: snapshot,
    label: `${enabled === "enabled" ? "$(check)" : "$(circle-slash)"} ${redactDisplayText(snapshot.name)}`,
    description: `${enabled} - ${transport} - ${source}`,
    detail: mcpServerDetail(snapshot)
  };
}

function mcpServerDetail(snapshot: McpServerSnapshotPayload): string {
  if ((snapshot.server.transport ?? "stdio") === "sse") {
    return redactDisplayText(snapshot.server.url ?? "No URL configured");
  }
  const command = [snapshot.server.command, ...(snapshot.server.args ?? [])].filter(Boolean).join(" ");
  return redactDisplayText(command || "No command configured");
}
