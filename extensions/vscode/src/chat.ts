import * as vscode from "vscode";

import {
  CodeGopherClient,
  CodeGopherClientError,
  type CodeGopherClientOptions,
  type Disposable,
  type StartTurnOptions
} from "./client";
import type { ProtocolEvent, TurnCompleteEvent } from "./protocol";

export const chatParticipantId = "codegopher.codegopher";
export const chatParticipantName = "codegopher";
export const chatOpenQuery = "@codegopher ";

export interface CodeGopherChatClient {
  readonly isRunning: boolean;
  startTurn(prompt: string, options?: StartTurnOptions): Promise<TurnCompleteEvent>;
  onEvent(listener: (event: ProtocolEvent) => void): Disposable;
}

export interface CodeGopherChatControllerOptions {
  outputChannel: vscode.OutputChannel;
  clientFactory?: () => CodeGopherChatClient;
  turnIdFactory?: () => string;
}

export class CodeGopherChatController {
  private readonly outputChannel: vscode.OutputChannel;
  private readonly clientFactory: () => CodeGopherChatClient;
  private readonly turnIdFactory: () => string;
  private client: CodeGopherChatClient | undefined;

  constructor(options: CodeGopherChatControllerOptions) {
    this.outputChannel = options.outputChannel;
    this.clientFactory = options.clientFactory ?? (() => this.createClientFromSettings());
    this.turnIdFactory = options.turnIdFactory ?? (() => `turn-${Date.now().toString(36)}`);
  }

  register(context: vscode.ExtensionContext): void {
    const participant = vscode.chat.createChatParticipant(chatParticipantId, (request, context, response, token) =>
      this.handleRequest(request, context, response, token)
    );
    participant.iconPath = new vscode.ThemeIcon("hubot");

    context.subscriptions.push(participant);
  }

  async openChat(): Promise<void> {
    try {
      await vscode.commands.executeCommand("workbench.action.chat.open", { query: chatOpenQuery });
    } catch {
      await vscode.commands.executeCommand("workbench.action.chat.open");
    }
  }

  async restart(): Promise<void> {
    this.outputChannel.appendLine("CodeGopher restart will be available after the chat client is wired.");
    await vscode.window.showInformationMessage("CodeGopher restart will be available after the chat client is wired.");
  }

  async handleRequest(
    request: vscode.ChatRequest,
    context: vscode.ChatContext,
    response: vscode.ChatResponseStream,
    token: vscode.CancellationToken
  ): Promise<vscode.ChatResult> {
    void context;
    void token;

    const turnId = this.turnIdFactory();
    const client = this.getClient();
    const subscription = client.onEvent((event) => {
      if (event.type === "text_delta" && event.turn_id === turnId) {
        response.markdown(event.content);
      }
    });

    try {
      await client.startTurn(request.prompt, {
        turnId,
        selectedFile: activeEditorPath(),
        editorMetadata: activeEditorMetadata()
      });
    } finally {
      subscription.dispose();
    }

    return {
      metadata: {
        command: request.command ?? null,
        participant: chatParticipantName,
        turnId
      }
    };
  }

  private getClient(): CodeGopherChatClient {
    this.client ??= this.clientFactory();
    return this.client;
  }

  private createClientFromSettings(): CodeGopherClient {
    const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
    if (!workspaceRoot) {
      throw new CodeGopherClientError("Open a workspace folder before using CodeGopher.");
    }

    const config = vscode.workspace.getConfiguration("codegopher");
    const options: CodeGopherClientOptions = {
      cliPath: config.get("cliPath", "cgopher"),
      workspaceRoot,
      provider: config.get("provider", ""),
      model: config.get("model", ""),
      baseUrl: config.get("baseUrl", ""),
      apiFamily: config.get("apiFamily", ""),
      approvalMode: config.get("approvalMode", ""),
      traceProtocol: config.get("traceProtocol", false),
      traceSink: (entry) => {
        this.outputChannel.appendLine(JSON.stringify(entry));
      }
    };
    return new CodeGopherClient(options);
  }
}

function activeEditorPath(): string | null {
  return vscode.window.activeTextEditor?.document.uri.fsPath ?? null;
}

function activeEditorMetadata(): Record<string, unknown> {
  const editor = vscode.window.activeTextEditor;
  if (!editor) {
    return {};
  }
  return {
    languageId: editor.document.languageId,
    uri: editor.document.uri.toString()
  };
}
