import * as vscode from "vscode";

import type { CodeGopherConfigClient } from "./client";
import type { ConfigSnapshotEvent, McpServerSnapshotPayload, McpServersEvent } from "./protocol";

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
      await this.dialogs.showQuickPick(formatMcpServerListItems(snapshot), {
        title: "CodeGopher MCP Servers",
        placeHolder: "Select a configured MCP server or add a new one"
      });
    } catch (error) {
      await this.dialogs.showErrorMessage(`CodeGopher MCP server management failed: ${errorMessage(error)}`);
    }
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
    showQuickPick: (items, options) => vscode.window.showQuickPick(items, options)
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
