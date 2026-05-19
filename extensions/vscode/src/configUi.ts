import * as vscode from "vscode";

import type { CodeGopherConfigClient } from "./client";
import type { ConfigSnapshotEvent } from "./protocol";

export interface CodeGopherConfigUiControllerOptions {
  clientProvider: () => CodeGopherConfigClient;
  dialogs?: CodeGopherConfigDialogs;
}

export interface CodeGopherConfigDialogs {
  showInformationMessage(message: string, ...items: string[]): PromiseLike<string | undefined>;
  showErrorMessage(message: string, ...items: string[]): PromiseLike<string | undefined>;
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
    showErrorMessage: (message, ...items) => vscode.window.showErrorMessage(message, ...items)
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
