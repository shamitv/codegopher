import * as assert from "node:assert/strict";

import { CodeGopherConfigUiController, formatEndpointDetails, formatMcpServerListItems } from "../../configUi";
import type { CodeGopherConfigClient } from "../../client";
import type { CodeGopherQuickPickItem } from "../../configUi";
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

  test("shows MCP add actions for an empty server list", async () => {
    const client = new FakeConfigClient();
    client.mcpServers = [];
    const dialogs = new FakeConfigDialogs();
    const controller = new CodeGopherConfigUiController({
      clientProvider: () => client,
      dialogs
    });

    await controller.manageMcpServers();

    assert.equal(client.listMcpServersCalls, 1);
    assert.equal(dialogs.quickPickCalls.length, 1);
    assert.deepEqual(
      dialogs.quickPickCalls[0]?.items.map((item) => item.label),
      ["$(add) Add stdio server", "$(add) Add SSE server"]
    );
  });

  test("formats MCP stdio and SSE server rows", () => {
    const items = formatMcpServerListItems({
      version: 1,
      type: "mcp_servers",
      workspace_root: "/repo",
      servers: [
        {
          name: "playwright",
          source: "project",
          server: {
            enabled: true,
            transport: "stdio",
            command: "npx",
            args: ["@playwright/mcp@latest"]
          }
        },
        {
          name: "docs",
          source: "user",
          server: {
            enabled: false,
            transport: "sse",
            url: "https://mcp.example.test/sse?token=raw-token"
          }
        }
      ]
    });

    assert.deepEqual(
      items.map((item) => item.label),
      ["$(add) Add stdio server", "$(add) Add SSE server", "$(check) playwright", "$(circle-slash) docs"]
    );
    assert.equal(items[2]?.description, "enabled - stdio - project");
    assert.equal(items[2]?.detail, "npx @playwright/mcp@latest");
    assert.equal(items[3]?.description, "disabled - sse - user");
    assert.equal(items[3]?.detail, "https://mcp.example.test/sse?token=[redacted]");
  });

  test("leaves MCP list selection cancellation alone", async () => {
    const client = new FakeConfigClient();
    const dialogs = new FakeConfigDialogs();
    const controller = new CodeGopherConfigUiController({
      clientProvider: () => client,
      dialogs
    });

    await controller.manageMcpServers();

    assert.equal(client.listMcpServersCalls, 1);
    assert.deepEqual(dialogs.informationMessages, []);
    assert.deepEqual(dialogs.errorMessages, []);
  });
});

class FakeConfigClient implements CodeGopherConfigClient {
  getEffectiveConfigCalls = 0;
  getEffectiveConfigError: Error | undefined;
  listMcpServersCalls = 0;
  mcpServers: McpServersEvent["servers"] = [
    {
      name: "playwright",
      source: "project",
      server: {
        enabled: true,
        transport: "stdio",
        command: "npx",
        args: ["@playwright/mcp@latest"]
      }
    }
  ];

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
    this.listMcpServersCalls += 1;
    return Promise.resolve({
      version: 1,
      type: "mcp_servers",
      workspace_root: "/repo",
      servers: this.mcpServers
    });
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
  readonly quickPickCalls: Array<{ items: readonly CodeGopherQuickPickItem[]; options: unknown }> = [];

  showInformationMessage(message: string): PromiseLike<string | undefined> {
    this.informationMessages.push(message);
    return Promise.resolve(undefined);
  }

  showErrorMessage(message: string): PromiseLike<string | undefined> {
    this.errorMessages.push(message);
    return Promise.resolve(undefined);
  }

  showQuickPick<T extends CodeGopherQuickPickItem>(
    items: readonly T[],
    options?: unknown
  ): PromiseLike<T | undefined> {
    this.quickPickCalls.push({ items, options });
    return Promise.resolve(undefined);
  }
}
