import * as assert from "node:assert/strict";

import * as vscode from "vscode";

import { chatParticipantId } from "../../chat";

const extensionId = "codegopher.codegopher-vscode";

const expectedCommands = [
  "codegopher.openChat",
  "codegopher.restartAgent",
  "codegopher.viewLlmEndpoint",
  "codegopher.manageMcpServers",
  "codegopher.showProtocolTrace"
] as const;

suite("CodeGopher extension", () => {
  test("activates the extension", async () => {
    const extension = vscode.extensions.getExtension(extensionId);

    assert.ok(extension, `Expected extension ${extensionId} to be available.`);
    await extension.activate();

    assert.equal(extension.isActive, true);
  });

  test("registers contributed commands", async () => {
    const commands = await vscode.commands.getCommands(true);

    for (const command of expectedCommands) {
      assert.ok(commands.includes(command), `Expected command ${command} to be registered.`);
    }
  });

  test("exposes configuration defaults", () => {
    const config = vscode.workspace.getConfiguration("codegopher");

    assert.equal(config.get("cliPath"), "cgopher");
    assert.equal(config.get("provider"), "");
    assert.equal(config.get("model"), "");
    assert.equal(config.get("baseUrl"), "");
    assert.equal(config.get("apiFamily"), "");
    assert.equal(config.get("approvalMode"), "");
    assert.equal(config.get("traceProtocol"), false);
  });

  test("contributes the CodeGopher chat participant", () => {
    const extension = vscode.extensions.getExtension(extensionId);
    assert.ok(extension, `Expected extension ${extensionId} to be available.`);

    const chatParticipants = extension.packageJSON.contributes.chatParticipants;
    assert.deepEqual(chatParticipants, [
      {
        id: chatParticipantId,
        name: "codegopher",
        fullName: "CodeGopher",
        description: "Ask CodeGopher about the current workspace.",
        isSticky: true,
        commands: [
          {
            name: "help",
            description: "Show CodeGopher help."
          },
          {
            name: "status",
            description: "Show CodeGopher status."
          },
          {
            name: "restart",
            description: "Restart the CodeGopher agent."
          }
        ]
      }
    ]);
  });
});
