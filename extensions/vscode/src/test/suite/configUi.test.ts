import * as assert from "node:assert/strict";

import { CodeGopherConfigUiController, formatEndpointDetails } from "../../configUi";
import type { CodeGopherConfigClient } from "../../client";
import type {
  ConfigSnapshotEvent,
  McpServerDeletedEvent,
  McpServerSavedEvent,
  McpServersEvent
} from "../../protocol";

suite("CodeGopher config UI", () => {
  test("requests effective config and shows endpoint details", async () => {
    const client = new FakeConfigClient();
    const dialogs = new FakeConfigDialogs();
    const controller = new CodeGopherConfigUiController({
      clientProvider: () => client,
      dialogs
    });

    await controller.viewLlmEndpoint();

    assert.equal(client.getEffectiveConfigCalls, 1);
    assert.deepEqual(dialogs.informationMessages, [
      [
        "CodeGopher LLM Endpoint",
        "Workspace: /repo",
        "Provider: openai",
        "Model: gpt-test",
        "API family: responses",
        "Base URL: https://api.example.test/v1",
        "Config sources: defaults, project"
      ].join("\n")
    ]);
    assert.deepEqual(dialogs.errorMessages, []);
  });

  test("formats missing endpoint details without secrets", () => {
    const details = formatEndpointDetails({
      version: 1,
      type: "config_snapshot",
      workspace_root: "/repo",
      provider: "local",
      model: "gpt-local",
      api_family: "chat_completions",
      base_url: null,
      config_sources: []
    });

    assert.match(details, /Base URL: Not configured/);
    assert.match(details, /Config sources: Not reported/);
  });

  test("redacts secret-like endpoint display values", () => {
    const details = formatEndpointDetails({
      version: 1,
      type: "config_snapshot",
      workspace_root: "/repo?token=raw-token",
      provider: "openai",
      model: "gpt-test",
      api_family: "responses",
      base_url: "https://user:raw-secret@example.test/v1?api_key=raw-key&token=raw-token",
      config_sources: ["project", "authorization=Bearer raw-auth"]
    });

    assert.doesNotMatch(details, /raw-token/);
    assert.doesNotMatch(details, /raw-key/);
    assert.doesNotMatch(details, /raw-secret/);
    assert.doesNotMatch(details, /raw-auth/);
    assert.match(details, /\[redacted\]/);
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
