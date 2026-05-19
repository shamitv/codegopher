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
const maxProgressSummaryLength = 160;

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
    const toolNames = new Map<string, string>();
    let reportedError: string | undefined;
    const subscription = client.onEvent((event) => {
      if (!("turn_id" in event) || event.turn_id !== turnId) {
        return;
      }
      if (event.type === "error") {
        reportedError = `${event.code}: ${event.message}`;
        writeChatError(response, reportedError);
        return;
      }
      if (event.type === "text_delta") {
        response.markdown(event.content);
        return;
      }
      if (event.type === "reasoning_delta") {
        this.outputChannel.appendLine(`CodeGopher reasoning update for ${turnId}.`);
        return;
      }
      if (event.type === "tool_call") {
        toolNames.set(event.tool_id, event.tool_name);
        response.progress(`Calling ${event.tool_name}${formatSummary(event.arguments_summary)}`);
        return;
      }
      if (event.type === "tool_result") {
        const toolName = toolNames.get(event.tool_id) ?? "tool";
        const state = event.is_error ? "failed" : "completed";
        response.progress(`${toolName} ${state}${formatSummary(event.result_summary)}`);
      }
    });

    try {
      await client.startTurn(request.prompt, {
        turnId,
        selectedFile: activeEditorPath(),
        editorMetadata: activeEditorMetadata()
      });
    } catch (error) {
      const message = reportedError ?? errorMessage(error);
      if (!reportedError) {
        writeChatError(response, message);
      }
      return {
        errorDetails: {
          message
        },
        metadata: {
          command: request.command ?? null,
          participant: chatParticipantName,
          turnId
        }
      };
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

function formatSummary(summary: string | undefined): string {
  if (!summary) {
    return "";
  }
  return `: ${truncateSummary(summary)}`;
}

function writeChatError(response: vscode.ChatResponseStream, message: string): void {
  response.markdown(`CodeGopher error: ${message}`);
}

function errorMessage(error: unknown): string {
  if (error instanceof Error && error.message) {
    return error.message;
  }
  return "CodeGopher request failed.";
}

export function truncateSummary(summary: string): string {
  const compact = summary.replace(/\s+/g, " ").trim();
  if (compact.length <= maxProgressSummaryLength) {
    return compact;
  }
  return `${compact.slice(0, maxProgressSummaryLength - 3)}...`;
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
