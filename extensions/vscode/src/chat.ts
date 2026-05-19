import * as vscode from "vscode";

import {
  CodeGopherClient,
  CodeGopherClientError,
  type CodeGopherConfigClient,
  type CodeGopherClientOptions,
  type Disposable,
  type StartTurnOptions
} from "./client";
import type { ProtocolEvent, TurnCompleteEvent } from "./protocol";
import type { SessionStartedEvent } from "./protocol";

export const chatParticipantId = "codegopher.codegopher";
export const chatParticipantName = "codegopher";
export const chatOpenQuery = "@codegopher ";
export const approvalApproveCommandId = "codegopher.approveApproval";
export const approvalDenyCommandId = "codegopher.denyApproval";
export const defaultApprovalDenialReason = "Denied from VS Code.";
const maxProgressSummaryLength = 160;

export interface CodeGopherChatClient {
  readonly isRunning: boolean;
  readonly sessionStarted?: SessionStartedEvent;
  startTurn(prompt: string, options?: StartTurnOptions): Promise<TurnCompleteEvent>;
  submitApproval(approvalId: string, approved: boolean, reason?: string | null): void;
  cancelTurn(turnId: string): void;
  restart(): Promise<SessionStartedEvent>;
  onEvent(listener: (event: ProtocolEvent) => void): Disposable;
}

export interface CodeGopherChatSettings {
  cliPath: string;
  provider: string;
  model: string;
  baseUrl: string;
  apiFamily: "" | "chat_completions" | "responses";
  approvalMode: "" | "review" | "auto" | "yolo";
  traceProtocol: boolean;
}

export interface CodeGopherChatControllerOptions {
  outputChannel: vscode.OutputChannel;
  clientFactory?: () => CodeGopherChatClient;
  settingsProvider?: () => CodeGopherChatSettings;
  workspaceRootProvider?: () => string | undefined;
  workspaceSelectionProvider?: () => WorkspaceSelection;
  turnIdFactory?: () => string;
}

export interface WorkspaceFolderInfo {
  readonly uri: {
    readonly fsPath: string;
  };
}

export interface WorkspaceSelection {
  selectedRoot: string | undefined;
  roots: string[];
  reason: "first-workspace-folder" | "no-workspace";
}

export class CodeGopherChatController {
  private readonly outputChannel: vscode.OutputChannel;
  private readonly clientFactory: () => CodeGopherChatClient;
  private readonly settingsProvider: () => CodeGopherChatSettings;
  private readonly workspaceSelectionProvider: () => WorkspaceSelection;
  private readonly turnIdFactory: () => string;
  private readonly pendingApprovals = new Map<string, PendingApproval>();
  private client: CodeGopherChatClient | undefined;

  constructor(options: CodeGopherChatControllerOptions) {
    this.outputChannel = options.outputChannel;
    this.clientFactory = options.clientFactory ?? (() => this.createClientFromSettings());
    this.settingsProvider = options.settingsProvider ?? readSettings;
    this.workspaceSelectionProvider =
      options.workspaceSelectionProvider ??
      (options.workspaceRootProvider
        ? () => workspaceSelectionFromRoot(options.workspaceRootProvider?.())
        : defaultWorkspaceSelection);
    this.turnIdFactory = options.turnIdFactory ?? (() => `turn-${Date.now().toString(36)}`);
  }

  register(context: vscode.ExtensionContext): void {
    const participant = vscode.chat.createChatParticipant(chatParticipantId, (request, context, response, token) =>
      this.handleRequest(request, context, response, token)
    );
    participant.iconPath = new vscode.ThemeIcon("hubot");

    context.subscriptions.push(
      participant,
      vscode.commands.registerCommand(approvalApproveCommandId, (approvalId: string) => this.approveApproval(approvalId)),
      vscode.commands.registerCommand(approvalDenyCommandId, (approvalId: string) => this.denyApproval(approvalId))
    );
  }

  async openChat(): Promise<void> {
    try {
      await vscode.commands.executeCommand("workbench.action.chat.open", { query: chatOpenQuery });
    } catch {
      await vscode.commands.executeCommand("workbench.action.chat.open");
    }
  }

  async restart(): Promise<void> {
    try {
      await this.restartAgent();
      this.outputChannel.appendLine("CodeGopher restarted.");
      void vscode.window.showInformationMessage("CodeGopher restarted.");
    } catch (error) {
      const message = errorMessage(error);
      this.outputChannel.appendLine(`CodeGopher restart failed: ${message}`);
      void vscode.window.showErrorMessage(`CodeGopher restart failed: ${message}`);
    }
  }

  approveApproval(approvalId: string): void {
    this.submitApprovalDecision(approvalId, true);
  }

  denyApproval(approvalId: string): void {
    this.submitApprovalDecision(approvalId, false, defaultApprovalDenialReason);
  }

  configClient(): CodeGopherConfigClient {
    return this.getClient() as unknown as CodeGopherConfigClient;
  }

  async handleRequest(
    request: vscode.ChatRequest,
    context: vscode.ChatContext,
    response: vscode.ChatResponseStream,
    token: vscode.CancellationToken
  ): Promise<vscode.ChatResult> {
    void context;

    if (request.command === "help") {
      response.markdown(helpMarkdown());
      return commandResult(request.command);
    }
    if (request.command === "status") {
      response.markdown(this.statusMarkdown());
      return commandResult(request.command);
    }
    if (request.command === "restart") {
      return this.handleRestartCommand(response);
    }

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
      if (event.type === "approval_request") {
        this.pendingApprovals.set(event.approval_id, { client, turnId });
        response.progress(`Approval required for ${event.tool_name}${formatSummary(event.arguments_summary)}`);
        response.button({
          command: approvalApproveCommandId,
          title: "Approve",
          arguments: [event.approval_id]
        });
        response.button({
          command: approvalDenyCommandId,
          title: "Deny",
          arguments: [event.approval_id]
        });
        return;
      }
      if (event.type === "tool_result") {
        const toolName = toolNames.get(event.tool_id) ?? "tool";
        const state = event.is_error ? "failed" : "completed";
        response.progress(`${toolName} ${state}${formatSummary(event.result_summary)}`);
      }
    });

    let cancellationSubscription: vscode.Disposable | undefined;
    let cancellationSent = false;
    const cancelCurrentTurn = () => {
      if (cancellationSent) {
        return;
      }
      cancellationSent = true;
      this.cancelActiveTurn(client, turnId);
    };

    try {
      const turn = client.startTurn(request.prompt, {
        turnId,
        selectedFile: activeEditorPath(),
        editorMetadata: activeEditorMetadata()
      });
      cancellationSubscription = token.onCancellationRequested(cancelCurrentTurn);
      if (token.isCancellationRequested) {
        cancelCurrentTurn();
      }
      await turn;
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
      cancellationSubscription?.dispose();
      subscription.dispose();
      this.clearTurnApprovals(turnId);
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

  private async handleRestartCommand(response: vscode.ChatResponseStream): Promise<vscode.ChatResult> {
    response.progress("Restarting CodeGopher...");
    try {
      const session = await this.restartAgent();
      response.markdown(`CodeGopher restarted with ${session.provider} / ${session.model}.`);
      return commandResult("restart");
    } catch (error) {
      const message = errorMessage(error);
      writeChatError(response, message);
      return {
        errorDetails: {
          message
        },
        metadata: {
          command: "restart",
          participant: chatParticipantName
        }
      };
    }
  }

  private restartAgent(): Promise<SessionStartedEvent> {
    return this.getClient().restart();
  }

  private submitApprovalDecision(approvalId: string, approved: boolean, reason?: string | null): void {
    const pending = this.pendingApprovals.get(approvalId);
    if (!pending) {
      this.outputChannel.appendLine(`CodeGopher approval ignored; no pending approval for ${approvalId}.`);
      return;
    }

    this.pendingApprovals.delete(approvalId);
    try {
      pending.client.submitApproval(approvalId, approved, reason);
    } catch (error) {
      this.outputChannel.appendLine(`CodeGopher approval failed for ${approvalId}: ${errorMessage(error)}`);
    }
  }

  private clearTurnApprovals(turnId: string): void {
    for (const [approvalId, pending] of this.pendingApprovals) {
      if (pending.turnId === turnId) {
        this.pendingApprovals.delete(approvalId);
      }
    }
  }

  private cancelActiveTurn(client: CodeGopherChatClient, turnId: string): void {
    try {
      client.cancelTurn(turnId);
      this.outputChannel.appendLine(`CodeGopher cancellation requested for ${turnId}.`);
    } catch (error) {
      this.outputChannel.appendLine(`CodeGopher cancellation failed for ${turnId}: ${errorMessage(error)}`);
    }
  }

  private createClientFromSettings(): CodeGopherClient {
    const workspace = this.workspaceSelectionProvider();
    const workspaceRoot = workspace.selectedRoot;
    if (!workspaceRoot) {
      throw new CodeGopherClientError("Open a workspace folder before using CodeGopher.");
    }

    const settings = this.settingsProvider();
    const options: CodeGopherClientOptions = {
      cliPath: settings.cliPath,
      workspaceRoot,
      provider: settings.provider,
      model: settings.model,
      baseUrl: settings.baseUrl,
      apiFamily: settings.apiFamily,
      approvalMode: settings.approvalMode,
      traceProtocol: settings.traceProtocol,
      traceSink: (entry) => {
        this.outputChannel.appendLine(JSON.stringify(entry));
      }
    };
    return new CodeGopherClient(options);
  }

  private statusMarkdown(): string {
    const settings = this.settingsProvider();
    const workspace = this.workspaceSelectionProvider();
    const workspaceRoot = workspace.selectedRoot;
    const session = this.client?.sessionStarted;
    const provider = (session?.provider ?? settings.provider) || "configured default";
    const model = (session?.model ?? settings.model) || "configured default";
    const approvalMode = (session?.approval_mode ?? settings.approvalMode) || "configured default";

    return [
      "**CodeGopher Status**",
      "",
      `- CLI: \`${settings.cliPath}\``,
      `- Workspace: \`${workspaceRoot ?? "No workspace folder"}\``,
      `- Workspace selection: ${formatWorkspaceSelection(workspace)}`,
      `- Subprocess: ${this.client?.isRunning ? "running" : "not started"}`,
      `- Provider: ${provider}`,
      `- Model: ${model}`,
      `- Approval mode: ${approvalMode}`,
      `- Protocol trace: ${settings.traceProtocol ? "enabled" : "disabled"}`
    ].join("\n");
  }
}

interface PendingApproval {
  client: CodeGopherChatClient;
  turnId: string;
}

function commandResult(command: string): vscode.ChatResult {
  return {
    metadata: {
      command,
      participant: chatParticipantName
    }
  };
}

function helpMarkdown(): string {
  return [
    "**CodeGopher**",
    "",
    "- Ask `@codegopher` questions about this workspace.",
    "- Use `/status` to inspect the CLI path, workspace root, model, and subprocess state.",
    "- Use `/restart` after changing settings or environment variables."
  ].join("\n");
}

function readSettings(): CodeGopherChatSettings {
  const config = vscode.workspace.getConfiguration("codegopher");
  return {
    cliPath: config.get("cliPath", "cgopher"),
    provider: config.get("provider", ""),
    model: config.get("model", ""),
    baseUrl: config.get("baseUrl", ""),
    apiFamily: config.get("apiFamily", ""),
    approvalMode: config.get("approvalMode", ""),
    traceProtocol: config.get("traceProtocol", false)
  };
}

export function selectWorkspaceRoot(workspaceFolders: readonly WorkspaceFolderInfo[] | undefined): WorkspaceSelection {
  const roots = [...(workspaceFolders ?? [])].map((folder) => folder.uri.fsPath);
  return {
    selectedRoot: roots[0],
    roots,
    reason: roots.length > 0 ? "first-workspace-folder" : "no-workspace"
  };
}

function defaultWorkspaceSelection(): WorkspaceSelection {
  return selectWorkspaceRoot(vscode.workspace.workspaceFolders);
}

function workspaceSelectionFromRoot(root: string | undefined): WorkspaceSelection {
  return {
    selectedRoot: root,
    roots: root ? [root] : [],
    reason: root ? "first-workspace-folder" : "no-workspace"
  };
}

function formatWorkspaceSelection(selection: WorkspaceSelection): string {
  if (!selection.selectedRoot) {
    return "No workspace folder is open";
  }
  return "first workspace folder";
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
