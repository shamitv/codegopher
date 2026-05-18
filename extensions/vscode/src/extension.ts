import * as vscode from "vscode";

const outputChannelName = "CodeGopher";

export function activate(context: vscode.ExtensionContext): void {
  const outputChannel = vscode.window.createOutputChannel(outputChannelName);

  context.subscriptions.push(
    outputChannel,
    vscode.commands.registerCommand("codegopher.openChat", () => openChat()),
    vscode.commands.registerCommand("codegopher.restartAgent", () =>
      showScaffoldMessage("CodeGopher agent restart will be available after the events client is wired.")
    ),
    vscode.commands.registerCommand("codegopher.viewLlmEndpoint", () =>
      showScaffoldMessage("CodeGopher endpoint details will be available after config inspection is wired.")
    ),
    vscode.commands.registerCommand("codegopher.manageMcpServers", () =>
      showScaffoldMessage("CodeGopher MCP server management will be available after config commands are wired.")
    ),
    vscode.commands.registerCommand("codegopher.showProtocolTrace", () => {
      outputChannel.show();
      outputChannel.appendLine("CodeGopher protocol tracing will be available after the events client is wired.");
    })
  );
}

export function deactivate(): void {
  // Reserved for future subprocess cleanup.
}

async function openChat(): Promise<void> {
  try {
    await vscode.commands.executeCommand("workbench.action.chat.open");
  } catch {
    await showScaffoldMessage("CodeGopher chat will be available after @codegopher is wired.");
  }
}

function showScaffoldMessage(message: string) {
  return vscode.window.showInformationMessage(message);
}
