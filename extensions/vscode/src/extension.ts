import * as vscode from "vscode";

import { CodeGopherChatController } from "./chat";
import { CodeGopherConfigUiController } from "./configUi";

const outputChannelName = "CodeGopher";
const apiKeySecretKey = "codegopher.apiKey";

export function activate(context: vscode.ExtensionContext): void {
  const outputChannel = vscode.window.createOutputChannel(outputChannelName);
  outputChannel.appendLine("CodeGopher extension activated.");
  const chatController = new CodeGopherChatController({
    outputChannel,
    apiKeyProvider: () => context.secrets.get(apiKeySecretKey)
  });
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
    vscode.commands.registerCommand("codegopher.setApiKey", () => {
      outputChannel.appendLine("Command invoked: codegopher.setApiKey.");
      return setApiKey(context, outputChannel);
    }),
    vscode.commands.registerCommand("codegopher.clearApiKey", () => {
      outputChannel.appendLine("Command invoked: codegopher.clearApiKey.");
      return clearApiKey(context, outputChannel);
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

async function setApiKey(context: vscode.ExtensionContext, outputChannel: vscode.OutputChannel): Promise<void> {
  const apiKey = await vscode.window.showInputBox({
    ignoreFocusOut: true,
    password: true,
    placeHolder: "sk-... or hf_...",
    prompt: "Enter the provider API key CodeGopher should pass to the CLI."
  });
  if (apiKey === undefined) {
    outputChannel.appendLine("CodeGopher API key update cancelled.");
    return;
  }

  const trimmedApiKey = apiKey.trim();
  if (!trimmedApiKey) {
    void vscode.window.showWarningMessage("CodeGopher API key was not changed.");
    outputChannel.appendLine("CodeGopher API key update skipped because no key was entered.");
    return;
  }

  await context.secrets.store(apiKeySecretKey, trimmedApiKey);
  outputChannel.appendLine("CodeGopher API key stored in VS Code Secret Storage.");
  await vscode.window.showInformationMessage("CodeGopher API key stored. Run CodeGopher: Restart Agent to use it.");
}

async function clearApiKey(context: vscode.ExtensionContext, outputChannel: vscode.OutputChannel): Promise<void> {
  await context.secrets.delete(apiKeySecretKey);
  outputChannel.appendLine("CodeGopher API key cleared from VS Code Secret Storage.");
  await vscode.window.showInformationMessage("CodeGopher API key cleared. Run CodeGopher: Restart Agent to apply.");
}
