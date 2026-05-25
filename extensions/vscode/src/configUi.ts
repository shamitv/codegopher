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
  showWarningMessage(
    message: string,
    options: CodeGopherMessageOptions,
    ...items: string[]
  ): PromiseLike<string | undefined>;
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

export interface CodeGopherMessageOptions {
  modal?: boolean;
}

export interface McpServerListItem extends CodeGopherQuickPickItem {
  itemType: "add_stdio" | "add_sse" | "server";
  serverName?: string;
  server?: McpServerSnapshotPayload;
}

export interface McpServerActionItem extends CodeGopherQuickPickItem {
  itemType: "edit" | "enable" | "disable" | "remove";
  server: McpServerSnapshotPayload;
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
      await this.dialogs.showErrorMessage(formatUserError("CodeGopher endpoint inspection failed", error));
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
      if (picked.itemType === "server" && picked.server) {
        await this.manageExistingServer(picked.server);
      }
    } catch (error) {
      await this.dialogs.showErrorMessage(formatUserError("CodeGopher MCP server management failed", error));
    }
  }

  private async manageExistingServer(server: McpServerSnapshotPayload): Promise<void> {
    const picked = await this.dialogs.showQuickPick(formatMcpServerActionItems(server), {
      title: `CodeGopher MCP Server: ${server.name}`,
      placeHolder: "Select an action"
    });
    if (!picked) {
      return;
    }
    if (picked.itemType === "edit") {
      await this.editMcpServer(server);
    }
    if (picked.itemType === "enable") {
      await this.setMcpServerEnabled(server, true);
    }
    if (picked.itemType === "disable") {
      await this.setMcpServerEnabled(server, false);
    }
    if (picked.itemType === "remove") {
      await this.removeMcpServer(server);
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

  private async editMcpServer(snapshot: McpServerSnapshotPayload): Promise<void> {
    if (hasSecretContainers(snapshot.server)) {
      await this.dialogs.showErrorMessage(
        "Editing MCP servers with env, headers, or headers_env is not supported in VS Code."
      );
      return;
    }
    if (snapshot.source !== "project") {
      const confirmed = await this.dialogs.showWarningMessage(
        `Editing ${snapshot.name} will create a project-local override.`,
        { modal: true },
        "Create Override"
      );
      if (confirmed !== "Create Override") {
        return;
      }
    }
    if ((snapshot.server.transport ?? "stdio") === "sse") {
      await this.editSseServer(snapshot);
      return;
    }
    await this.editStdioServer(snapshot);
  }

  private async editStdioServer(snapshot: McpServerSnapshotPayload): Promise<void> {
    const command = await this.promptRequiredText(
      "Command",
      "Command used to launch the MCP server",
      "npx",
      snapshot.server.command ?? ""
    );
    if (!command) {
      return;
    }
    const argsText = await this.dialogs.showInputBox({
      title: "Arguments",
      prompt: "JSON string array of command arguments",
      placeHolder: "[\"@modelcontextprotocol/server-filesystem\", \".\"]",
      value: JSON.stringify(snapshot.server.args ?? []),
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
      value: snapshot.server.cwd ?? "",
      ignoreFocusOut: true
    });
    if (cwd === undefined) {
      return;
    }
    const startupTimeoutText = await this.dialogs.showInputBox({
      title: "Startup timeout",
      prompt: "Optional positive startup timeout in seconds",
      placeHolder: "30",
      value: formatOptionalNumber(snapshot.server.startup_timeout_seconds),
      ignoreFocusOut: true
    });
    if (startupTimeoutText === undefined) {
      return;
    }
    const startupTimeout = parseOptionalPositiveNumber(startupTimeoutText, "Startup timeout");
    const server: McpServerPayload = {
      enabled: snapshot.server.enabled !== false,
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
    await this.clientProvider().saveMcpServer(snapshot.name, server);
    await this.dialogs.showInformationMessage(`CodeGopher MCP server saved: ${snapshot.name}`);
  }

  private async setMcpServerEnabled(snapshot: McpServerSnapshotPayload, enabled: boolean): Promise<void> {
    if (!(await this.isProjectServer(snapshot))) {
      return;
    }
    await this.clientProvider().setMcpServerEnabled(snapshot.name, enabled);
    await this.dialogs.showInformationMessage(
      `CodeGopher MCP server ${enabled ? "enabled" : "disabled"}: ${snapshot.name}`
    );
  }

  private async removeMcpServer(snapshot: McpServerSnapshotPayload): Promise<void> {
    if (!(await this.isProjectServer(snapshot))) {
      return;
    }
    const confirmed = await this.dialogs.showWarningMessage(
      `Remove MCP server ${snapshot.name}?`,
      { modal: true },
      "Remove"
    );
    if (confirmed !== "Remove") {
      return;
    }
    await this.clientProvider().deleteMcpServer(snapshot.name);
    await this.dialogs.showInformationMessage(`CodeGopher MCP server removed: ${snapshot.name}`);
  }

  private async isProjectServer(snapshot: McpServerSnapshotPayload): Promise<boolean> {
    if (snapshot.source === "project") {
      return true;
    }
    await this.dialogs.showErrorMessage("Only project-local MCP servers can be enabled, disabled, or removed.");
    return false;
  }

  private async editSseServer(snapshot: McpServerSnapshotPayload): Promise<void> {
    const url = await this.promptRequiredText(
      "URL",
      "SSE URL for the MCP server",
      "https://example.test/sse",
      snapshot.server.url ?? ""
    );
    if (!url) {
      return;
    }
    const timeoutText = await this.dialogs.showInputBox({
      title: "Request timeout",
      prompt: "Optional positive request timeout in seconds",
      placeHolder: "5",
      value: formatOptionalNumber(snapshot.server.timeout_seconds),
      ignoreFocusOut: true
    });
    if (timeoutText === undefined) {
      return;
    }
    const readTimeoutText = await this.dialogs.showInputBox({
      title: "SSE read timeout",
      prompt: "Optional positive SSE read timeout in seconds",
      placeHolder: "300",
      value: formatOptionalNumber(snapshot.server.sse_read_timeout_seconds),
      ignoreFocusOut: true
    });
    if (readTimeoutText === undefined) {
      return;
    }
    const timeout = parseOptionalPositiveNumber(timeoutText, "Request timeout");
    const readTimeout = parseOptionalPositiveNumber(readTimeoutText, "SSE read timeout");
    const server: McpServerPayload = {
      enabled: snapshot.server.enabled !== false,
      transport: "sse",
      url
    };
    if (timeout !== undefined) {
      server.timeout_seconds = timeout;
    }
    if (readTimeout !== undefined) {
      server.sse_read_timeout_seconds = readTimeout;
    }
    await this.clientProvider().saveMcpServer(snapshot.name, server);
    await this.dialogs.showInformationMessage(`CodeGopher MCP server saved: ${snapshot.name}`);
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
    placeHolder: string,
    initialValue?: string
  ): Promise<string | undefined> {
    const value = await this.dialogs.showInputBox({
      title,
      prompt,
      placeHolder,
      value: initialValue,
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
    `Replay reasoning content: ${snapshot.replay_reasoning_content ? "enabled" : "disabled"}`,
    `Config sources: ${formatConfigSources(snapshot.config_sources)}`
  ].join("\n");
}

function defaultDialogs(): CodeGopherConfigDialogs {
  return {
    showInformationMessage: (message, ...items) => vscode.window.showInformationMessage(message, ...items),
    showErrorMessage: (message, ...items) => vscode.window.showErrorMessage(message, ...items),
    showWarningMessage: (message, options, ...items) => vscode.window.showWarningMessage(message, options, ...items),
    showQuickPick: (items, options) => vscode.window.showQuickPick(items, options),
    showInputBox: (options) => vscode.window.showInputBox(options)
  };
}

export function formatUserError(prefix: string, error: unknown): string {
  return `${prefix}: ${redactDisplayText(errorMessage(error))}`;
}

function formatConfigSources(sources: string[] | undefined): string {
  if (!sources || sources.length === 0) {
    return "Not reported";
  }
  return sources.map((source) => redactDisplayText(source)).join(", ");
}

export function redactDisplayText(value: string): string {
  return value
    .replace(
      /((?:api[_-]?key|authorization|password|passwd|secret|token|credential)\s*[:=]\s*)(?:bearer\s+)?[^&\s,;]+/gi,
      "$1[redacted]"
    )
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

export function formatMcpServerActionItems(snapshot: McpServerSnapshotPayload): McpServerActionItem[] {
  const enabled = snapshot.server.enabled !== false;
  return [
    {
      itemType: "edit",
      server: snapshot,
      label: "$(edit) Edit server",
      description: "non-secret fields",
      detail: "Update project-local settings through Python validation"
    },
    {
      itemType: enabled ? "disable" : "enable",
      server: snapshot,
      label: enabled ? "$(debug-pause) Disable server" : "$(debug-start) Enable server",
      description: "project only",
      detail: "Update the project-local enabled state"
    },
    {
      itemType: "remove",
      server: snapshot,
      label: "$(trash) Remove server",
      description: "project only",
      detail: "Delete the project-local MCP server entry"
    }
  ];
}

export function hasSecretContainers(server: McpServerPayload): boolean {
  return hasRecordValues(server.env) || hasRecordValues(server.headers) || hasRecordValues(server.headers_env);
}

function hasRecordValues(value: Record<string, string> | undefined): boolean {
  return value !== undefined && Object.keys(value).length > 0;
}

function formatOptionalNumber(value: number | undefined): string {
  return value === undefined ? "" : String(value);
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

function errorMessage(error: unknown): string {
  if (error instanceof Error && error.message) {
    return error.message;
  }
  return "CodeGopher request failed.";
}
