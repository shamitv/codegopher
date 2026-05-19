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
      await this.dialogs.showInformationMessage(formatEndpointSummary(snapshot));
    } catch (error) {
      await this.dialogs.showErrorMessage(`CodeGopher endpoint inspection failed: ${errorMessage(error)}`);
    }
  }
}

export function formatEndpointSummary(snapshot: ConfigSnapshotEvent): string {
  return `CodeGopher endpoint: ${snapshot.provider} / ${snapshot.model}`;
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
