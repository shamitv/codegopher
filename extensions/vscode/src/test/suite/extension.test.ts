import * as assert from "node:assert/strict";

import * as vscode from "vscode";

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
});
