import * as assert from "node:assert/strict";

import { CodeGopherConfigUiController } from "../../configUi";
import type { CodeGopherConfigClient } from "../../client";
import type {
  ConfigSnapshotEvent,
  McpServerDeletedEvent,
  McpServerSavedEvent,
  McpServersEvent
} from "../../protocol";

suite("CodeGopher config UI", () => {
  test("requests effective config and shows an endpoint summary", async () => {
    const client = new FakeConfigClient();
    const dialogs = new FakeConfigDialogs();
    const controller = new CodeGopherConfigUiController({
      clientProvider: () => client,
      dialogs
    });

    await controller.viewLlmEndpoint();

    assert.equal(client.getEffectiveConfigCalls, 1);
    assert.deepEqual(dialogs.informationMessages, ["CodeGopher endpoint: openai / gpt-test"]);
    assert.deepEqual(dialogs.errorMessages, []);
  });

  test("shows endpoint request errors", async () => {
    const client = new FakeConfigClient();
    client.getEffectiveConfigError = new Error("configuration_error: Invalid settings");
    const dialogs = new FakeConfigDialogs();
    const controller = new CodeGopherConfigUiController({
      clientProvider: () => client,
      dialogs
    });

    await controller.viewLlmEndpoint();

    assert.deepEqual(dialogs.informationMessages, []);
    assert.deepEqual(dialogs.errorMessages, [
      "CodeGopher endpoint inspection failed: configuration_error: Invalid settings"
    ]);
  });
});

class FakeConfigClient implements CodeGopherConfigClient {
  getEffectiveConfigCalls = 0;
  getEffectiveConfigError: Error | undefined;

  getEffectiveConfig(): Promise<ConfigSnapshotEvent> {
    this.getEffectiveConfigCalls += 1;
    if (this.getEffectiveConfigError) {
      return Promise.reject(this.getEffectiveConfigError);
    }
    return Promise.resolve({
      version: 1,
      type: "config_snapshot",
      workspace_root: "/repo",
      provider: "openai",
      model: "gpt-test",
      api_family: "responses",
      base_url: "https://api.example.test/v1",
      config_sources: ["defaults", "project"]
    });
  }

  listMcpServers(): Promise<McpServersEvent> {
    throw new Error("Not implemented.");
  }

  saveMcpServer(): Promise<McpServerSavedEvent> {
    throw new Error("Not implemented.");
  }

  setMcpServerEnabled(): Promise<McpServerSavedEvent> {
    throw new Error("Not implemented.");
  }

  deleteMcpServer(): Promise<McpServerDeletedEvent> {
    throw new Error("Not implemented.");
  }
}

class FakeConfigDialogs {
  readonly informationMessages: string[] = [];
  readonly errorMessages: string[] = [];

  showInformationMessage(message: string): PromiseLike<string | undefined> {
    this.informationMessages.push(message);
    return Promise.resolve(undefined);
  }

  showErrorMessage(message: string): PromiseLike<string | undefined> {
    this.errorMessages.push(message);
    return Promise.resolve(undefined);
  }
}
