import * as vscode from "vscode";

import { CodeGopherChatController } from "./chat";
import { CodeGopherConfigUiController } from "./configUi";

const outputChannelName = "CodeGopher";

export function activate(context: vscode.ExtensionContext): void {
  const outputChannel = vscode.window.createOutputChannel(outputChannelName);
  const chatController = new CodeGopherChatController({ outputChannel });
  const configUiController = new CodeGopherConfigUiController({
    clientProvider: () => chatController.configClient()
  });
  chatController.register(context);

  context.subscriptions.push(
    outputChannel,
    vscode.commands.registerCommand("codegopher.openChat", () => chatController.openChat()),
    vscode.commands.registerCommand("codegopher.restartAgent", () => chatController.restart()),
    vscode.commands.registerCommand("codegopher.viewLlmEndpoint", () => configUiController.viewLlmEndpoint()),
    vscode.commands.registerCommand("codegopher.manageMcpServers", () => configUiController.manageMcpServers()),
    vscode.commands.registerCommand("codegopher.showProtocolTrace", () => {
      outputChannel.show();
      outputChannel.appendLine("CodeGopher protocol tracing will be available after the events client is wired.");
    })
  );
}

export function deactivate(): void {
  // Reserved for future subprocess cleanup.
}
