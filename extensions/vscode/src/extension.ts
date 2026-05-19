import * as vscode from "vscode";

import { CodeGopherChatController } from "./chat";
import { CodeGopherConfigUiController } from "./configUi";

const outputChannelName = "CodeGopher";

export function activate(context: vscode.ExtensionContext): void {
  const outputChannel = vscode.window.createOutputChannel(outputChannelName);
  outputChannel.appendLine("CodeGopher extension activated.");
  const chatController = new CodeGopherChatController({ outputChannel });
  const configUiController = new CodeGopherConfigUiController({
    clientProvider: () => chatController.configClient()
  });
  chatController.register(context);

  context.subscriptions.push(
    outputChannel,
    vscode.commands.registerCommand("codegopher.openChat", () => {
      outputChannel.appendLine("Command invoked: codegopher.openChat.");
      return chatController.openChat();
    }),
    vscode.commands.registerCommand("codegopher.restartAgent", () => {
      outputChannel.appendLine("Command invoked: codegopher.restartAgent.");
      return chatController.restart();
    }),
    vscode.commands.registerCommand("codegopher.viewLlmEndpoint", () => {
      outputChannel.appendLine("Command invoked: codegopher.viewLlmEndpoint.");
      return configUiController.viewLlmEndpoint();
    }),
    vscode.commands.registerCommand("codegopher.manageMcpServers", () => {
      outputChannel.appendLine("Command invoked: codegopher.manageMcpServers.");
      return configUiController.manageMcpServers();
    }),
    vscode.commands.registerCommand("codegopher.showProtocolTrace", () => {
      outputChannel.appendLine("Command invoked: codegopher.showProtocolTrace.");
      outputChannel.show();
      outputChannel.appendLine("CodeGopher protocol tracing will be available after the events client is wired.");
    })
  );
  outputChannel.appendLine("CodeGopher commands registered.");
}

export function deactivate(): void {
  // Reserved for future subprocess cleanup.
}
