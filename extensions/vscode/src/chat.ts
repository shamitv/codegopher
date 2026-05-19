import * as vscode from "vscode";

export const chatParticipantId = "codegopher.codegopher";
export const chatParticipantName = "codegopher";
export const chatOpenQuery = "@codegopher ";

export class CodeGopherChatController {
  private readonly outputChannel: vscode.OutputChannel;

  constructor(outputChannel: vscode.OutputChannel) {
    this.outputChannel = outputChannel;
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

  private handleRequest(
    request: vscode.ChatRequest,
    _context: vscode.ChatContext,
    response: vscode.ChatResponseStream,
    _token: vscode.CancellationToken
  ): vscode.ProviderResult<vscode.ChatResult> {
    void _context;
    void _token;

    response.markdown("CodeGopher chat is ready. Agent streaming will be available next.");

    return {
      metadata: {
        command: request.command ?? null,
        participant: chatParticipantName
      }
    };
  }
}
