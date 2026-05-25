import * as assert from "node:assert/strict";

import {
  CodeGopherConfigUiController,
  formatEndpointDetails,
  formatMcpServerActionItems,
  formatMcpServerListItems,
  formatUserError,
  hasSecretContainers,
  parseJsonStringArray,
  parseOptionalPositiveNumber,
  validateMcpServerName
} from "../../configUi";
import type { CodeGopherConfigClient } from "../../client";
import type { CodeGopherQuickPickItem } from "../../configUi";
import type {
  ConfigSnapshotEvent,
  McpServerDeletedEvent,
  McpServerPayload,
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
        "Replay reasoning content: enabled",
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
    assert.match(details, /Replay reasoning content: disabled/);
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

  test("redacts endpoint request errors", async () => {
    const client = new FakeConfigClient();
    client.getEffectiveConfigError = new Error("configuration_error: api_key=raw-key Authorization: Bearer raw-token");
    const dialogs = new FakeConfigDialogs();
    const controller = new CodeGopherConfigUiController({
      clientProvider: () => client,
      dialogs
    });

    await controller.viewLlmEndpoint();

    assert.doesNotMatch(dialogs.errorMessages[0] ?? "", /raw-key/);
    assert.doesNotMatch(dialogs.errorMessages[0] ?? "", /raw-token/);
    assert.match(dialogs.errorMessages[0] ?? "", /\[redacted\]/);
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

  test("creates a stdio MCP server from prompts", async () => {
    const client = new FakeConfigClient();
    const dialogs = new FakeConfigDialogs();
    dialogs.quickPickSelectionLabels.push("$(add) Add stdio server");
    dialogs.inputValues.push("playwright", "npx", "[\"@playwright/mcp@latest\"]", "/repo", "45");
    const controller = new CodeGopherConfigUiController({
      clientProvider: () => client,
      dialogs
    });

    await controller.manageMcpServers();

    assert.deepEqual(client.saveMcpServerCalls, [
      {
        serverName: "playwright",
        server: {
          enabled: true,
          transport: "stdio",
          command: "npx",
          args: ["@playwright/mcp@latest"],
          cwd: "/repo",
          startup_timeout_seconds: 45
        }
      }
    ]);
    assert.deepEqual(dialogs.informationMessages, ["CodeGopher MCP server saved: playwright"]);
  });

  test("creates an SSE MCP server from prompts", async () => {
    const client = new FakeConfigClient();
    const dialogs = new FakeConfigDialogs();
    dialogs.quickPickSelectionLabels.push("$(add) Add SSE server");
    dialogs.inputValues.push("docs", "https://mcp.example.test/sse", "10", "600");
    const controller = new CodeGopherConfigUiController({
      clientProvider: () => client,
      dialogs
    });

    await controller.manageMcpServers();

    assert.deepEqual(client.saveMcpServerCalls, [
      {
        serverName: "docs",
        server: {
          enabled: true,
          transport: "sse",
          url: "https://mcp.example.test/sse",
          timeout_seconds: 10,
          sse_read_timeout_seconds: 600
        }
      }
    ]);
    assert.deepEqual(dialogs.informationMessages, ["CodeGopher MCP server saved: docs"]);
  });

  test("cancels MCP creation when an input is cancelled", async () => {
    const client = new FakeConfigClient();
    const dialogs = new FakeConfigDialogs();
    dialogs.quickPickSelectionLabels.push("$(add) Add stdio server");
    dialogs.inputValues.push("playwright", undefined);
    const controller = new CodeGopherConfigUiController({
      clientProvider: () => client,
      dialogs
    });

    await controller.manageMcpServers();

    assert.deepEqual(client.saveMcpServerCalls, []);
    assert.deepEqual(dialogs.errorMessages, []);
  });

  test("rejects invalid MCP creation inputs before sending to Python", async () => {
    const client = new FakeConfigClient();
    const dialogs = new FakeConfigDialogs();
    dialogs.quickPickSelectionLabels.push("$(add) Add stdio server");
    dialogs.inputValues.push("bad.name");
    const controller = new CodeGopherConfigUiController({
      clientProvider: () => client,
      dialogs
    });

    await controller.manageMcpServers();

    assert.deepEqual(client.saveMcpServerCalls, []);
    assert.deepEqual(dialogs.errorMessages, ["MCP server names may contain only letters, numbers, '_' and '-'."]);
  });

  test("surfaces invalid MCP creation argument JSON", async () => {
    const client = new FakeConfigClient();
    const dialogs = new FakeConfigDialogs();
    dialogs.quickPickSelectionLabels.push("$(add) Add stdio server");
    dialogs.inputValues.push("playwright", "npx", "{not-json");
    const controller = new CodeGopherConfigUiController({
      clientProvider: () => client,
      dialogs
    });

    await controller.manageMcpServers();

    assert.deepEqual(client.saveMcpServerCalls, []);
    assert.match(dialogs.errorMessages[0] ?? "", /Arguments must be a JSON string array/);
  });

  test("redacts MCP list request errors", async () => {
    const client = new FakeConfigClient();
    client.listMcpServersError = new Error("configuration_error: token=raw-token password: raw-password");
    const dialogs = new FakeConfigDialogs();
    const controller = new CodeGopherConfigUiController({
      clientProvider: () => client,
      dialogs
    });

    await controller.manageMcpServers();

    assert.deepEqual(client.saveMcpServerCalls, []);
    assert.doesNotMatch(dialogs.errorMessages[0] ?? "", /raw-token/);
    assert.doesNotMatch(dialogs.errorMessages[0] ?? "", /raw-password/);
    assert.match(dialogs.errorMessages[0] ?? "", /\[redacted\]/);
  });

  test("edits a project-local stdio MCP server", async () => {
    const client = new FakeConfigClient();
    const dialogs = new FakeConfigDialogs();
    dialogs.quickPickSelectionLabels.push("$(check) playwright", "$(edit) Edit server");
    dialogs.inputValues.push("pnpm", "[\"exec\", \"playwright-mcp\"]", "/repo/tools", "60");
    const controller = new CodeGopherConfigUiController({
      clientProvider: () => client,
      dialogs
    });

    await controller.manageMcpServers();

    assert.deepEqual(client.saveMcpServerCalls, [
      {
        serverName: "playwright",
        server: {
          enabled: true,
          transport: "stdio",
          command: "pnpm",
          args: ["exec", "playwright-mcp"],
          cwd: "/repo/tools",
          startup_timeout_seconds: 60
        }
      }
    ]);
  });

  test("redacts MCP save errors", async () => {
    const client = new FakeConfigClient();
    client.saveMcpServerError = new Error("configuration_error: headers Authorization=Bearer raw-token");
    const dialogs = new FakeConfigDialogs();
    dialogs.quickPickSelectionLabels.push("$(add) Add SSE server");
    dialogs.inputValues.push("docs", "https://mcp.example.test/sse", "", "");
    const controller = new CodeGopherConfigUiController({
      clientProvider: () => client,
      dialogs
    });

    await controller.manageMcpServers();

    assert.doesNotMatch(dialogs.errorMessages[0] ?? "", /raw-token/);
    assert.match(dialogs.errorMessages[0] ?? "", /\[redacted\]/);
  });

  test("edits an SSE MCP server", async () => {
    const client = new FakeConfigClient();
    client.mcpServers = [
      {
        name: "docs",
        source: "project",
        server: {
          enabled: false,
          transport: "sse",
          url: "https://old.example.test/sse",
          timeout_seconds: 5,
          sse_read_timeout_seconds: 300
        }
      }
    ];
    const dialogs = new FakeConfigDialogs();
    dialogs.quickPickSelectionLabels.push("$(circle-slash) docs", "$(edit) Edit server");
    dialogs.inputValues.push("https://new.example.test/sse", "10", "600");
    const controller = new CodeGopherConfigUiController({
      clientProvider: () => client,
      dialogs
    });

    await controller.manageMcpServers();

    assert.deepEqual(client.saveMcpServerCalls, [
      {
        serverName: "docs",
        server: {
          enabled: false,
          transport: "sse",
          url: "https://new.example.test/sse",
          timeout_seconds: 10,
          sse_read_timeout_seconds: 600
        }
      }
    ]);
  });

  test("blocks editing MCP servers with secret-bearing containers", async () => {
    const client = new FakeConfigClient();
    client.mcpServers = [
      {
        name: "secure",
        source: "project",
        server: {
          enabled: true,
          transport: "sse",
          url: "https://mcp.example.test/sse",
          headers: { Authorization: "[redacted]" }
        }
      }
    ];
    const dialogs = new FakeConfigDialogs();
    dialogs.quickPickSelectionLabels.push("$(check) secure", "$(edit) Edit server");
    const controller = new CodeGopherConfigUiController({
      clientProvider: () => client,
      dialogs
    });

    await controller.manageMcpServers();

    assert.deepEqual(client.saveMcpServerCalls, []);
    assert.deepEqual(dialogs.errorMessages, [
      "Editing MCP servers with env, headers, or headers_env is not supported in VS Code."
    ]);
  });

  test("confirms before editing a non-project MCP server", async () => {
    const client = new FakeConfigClient();
    client.mcpServers = [
      {
        name: "global_docs",
        source: "user",
        server: {
          enabled: true,
          transport: "sse",
          url: "https://old.example.test/sse"
        }
      }
    ];
    const dialogs = new FakeConfigDialogs();
    dialogs.quickPickSelectionLabels.push("$(check) global_docs", "$(edit) Edit server");
    dialogs.warningSelections.push("Create Override");
    dialogs.inputValues.push("https://project.example.test/sse", "", "");
    const controller = new CodeGopherConfigUiController({
      clientProvider: () => client,
      dialogs
    });

    await controller.manageMcpServers();

    assert.equal(dialogs.warningMessages[0]?.message, "Editing global_docs will create a project-local override.");
    assert.deepEqual(client.saveMcpServerCalls, [
      {
        serverName: "global_docs",
        server: {
          enabled: true,
          transport: "sse",
          url: "https://project.example.test/sse"
        }
      }
    ]);
  });

  test("cancels non-project MCP edit overrides", async () => {
    const client = new FakeConfigClient();
    client.mcpServers = [
      {
        name: "global_docs",
        source: "user",
        server: {
          enabled: true,
          transport: "sse",
          url: "https://old.example.test/sse"
        }
      }
    ];
    const dialogs = new FakeConfigDialogs();
    dialogs.quickPickSelectionLabels.push("$(check) global_docs", "$(edit) Edit server");
    const controller = new CodeGopherConfigUiController({
      clientProvider: () => client,
      dialogs
    });

    await controller.manageMcpServers();

    assert.deepEqual(client.saveMcpServerCalls, []);
  });

  test("disables and enables project-local MCP servers", async () => {
    const client = new FakeConfigClient();
    const disableDialogs = new FakeConfigDialogs();
    disableDialogs.quickPickSelectionLabels.push("$(check) playwright", "$(debug-pause) Disable server");
    const disableController = new CodeGopherConfigUiController({
      clientProvider: () => client,
      dialogs: disableDialogs
    });

    await disableController.manageMcpServers();

    assert.deepEqual(client.setMcpServerEnabledCalls, [{ serverName: "playwright", enabled: false }]);
    assert.deepEqual(disableDialogs.informationMessages, ["CodeGopher MCP server disabled: playwright"]);

    client.mcpServers = [
      {
        name: "playwright",
        source: "project",
        server: {
          enabled: false,
          transport: "stdio",
          command: "npx"
        }
      }
    ];
    const enableDialogs = new FakeConfigDialogs();
    enableDialogs.quickPickSelectionLabels.push("$(circle-slash) playwright", "$(debug-start) Enable server");
    const enableController = new CodeGopherConfigUiController({
      clientProvider: () => client,
      dialogs: enableDialogs
    });

    await enableController.manageMcpServers();

    assert.deepEqual(client.setMcpServerEnabledCalls, [
      { serverName: "playwright", enabled: false },
      { serverName: "playwright", enabled: true }
    ]);
    assert.deepEqual(enableDialogs.informationMessages, ["CodeGopher MCP server enabled: playwright"]);
  });

  test("removes project-local MCP servers after confirmation", async () => {
    const client = new FakeConfigClient();
    const dialogs = new FakeConfigDialogs();
    dialogs.quickPickSelectionLabels.push("$(check) playwright", "$(trash) Remove server");
    dialogs.warningSelections.push("Remove");
    const controller = new CodeGopherConfigUiController({
      clientProvider: () => client,
      dialogs
    });

    await controller.manageMcpServers();

    assert.deepEqual(client.deleteMcpServerCalls, ["playwright"]);
    assert.deepEqual(dialogs.warningMessages[0], {
      message: "Remove MCP server playwright?",
      options: { modal: true },
      items: ["Remove"]
    });
    assert.deepEqual(dialogs.informationMessages, ["CodeGopher MCP server removed: playwright"]);
  });

  test("cancels MCP server removal", async () => {
    const client = new FakeConfigClient();
    const dialogs = new FakeConfigDialogs();
    dialogs.quickPickSelectionLabels.push("$(check) playwright", "$(trash) Remove server");
    const controller = new CodeGopherConfigUiController({
      clientProvider: () => client,
      dialogs
    });

    await controller.manageMcpServers();

    assert.deepEqual(client.deleteMcpServerCalls, []);
  });

  test("blocks enable disable remove for non-project MCP servers", async () => {
    const client = new FakeConfigClient();
    client.mcpServers = [
      {
        name: "global_docs",
        source: "user",
        server: {
          enabled: true,
          transport: "sse",
          url: "https://old.example.test/sse"
        }
      }
    ];
    const dialogs = new FakeConfigDialogs();
    dialogs.quickPickSelectionLabels.push("$(check) global_docs", "$(debug-pause) Disable server");
    const controller = new CodeGopherConfigUiController({
      clientProvider: () => client,
      dialogs
    });

    await controller.manageMcpServers();

    assert.deepEqual(client.setMcpServerEnabledCalls, []);
    assert.deepEqual(client.deleteMcpServerCalls, []);
    assert.deepEqual(dialogs.errorMessages, ["Only project-local MCP servers can be enabled, disabled, or removed."]);
  });

  test("parses creation helper values", () => {
    assert.equal(validateMcpServerName("ok-name_1"), undefined);
    assert.equal(validateMcpServerName("bad.name"), "MCP server names may contain only letters, numbers, '_' and '-'.");
    assert.deepEqual(parseJsonStringArray("[\"a\", \"b\"]", "Arguments"), ["a", "b"]);
    assert.deepEqual(parseJsonStringArray("", "Arguments"), []);
    assert.equal(parseOptionalPositiveNumber("2.5", "Timeout"), 2.5);
    assert.equal(parseOptionalPositiveNumber("", "Timeout"), undefined);
    assert.throws(() => parseJsonStringArray("[1]", "Arguments"), /Arguments must be a JSON string array/);
    assert.throws(() => parseOptionalPositiveNumber("0", "Timeout"), /Timeout must be a positive number/);
  });

  test("formats user errors with redaction", () => {
    const message = formatUserError(
      "Prefix",
      new Error("provider failed with credential: raw-credential and Bearer raw-token")
    );

    assert.equal(message, "Prefix: provider failed with credential: [redacted] and Bearer [redacted]");
  });

  test("formats MCP action rows and detects secret containers", () => {
    const [item] = formatMcpServerActionItems({
      name: "playwright",
      source: "project",
      server: { transport: "stdio", command: "npx" }
    });

    assert.equal(item?.label, "$(edit) Edit server");
    assert.deepEqual(
      formatMcpServerActionItems({
        name: "docs",
        source: "project",
        server: { enabled: false, transport: "sse", url: "https://example.test/sse" }
      }).map((action) => action.label),
      ["$(edit) Edit server", "$(debug-start) Enable server", "$(trash) Remove server"]
    );
    assert.equal(hasSecretContainers({ transport: "stdio", command: "npx" }), false);
    assert.equal(hasSecretContainers({ transport: "stdio", command: "npx", env: { TOKEN: "[redacted]" } }), true);
    assert.equal(
      hasSecretContainers({ transport: "sse", url: "https://example.test/sse", headers_env: { Auth: "[redacted]" } }),
      true
    );
  });
});

interface SaveMcpServerCall {
  serverName: string;
  server: McpServerPayload;
}

interface SetMcpServerEnabledCall {
  serverName: string;
  enabled: boolean;
}

class FakeConfigClient implements CodeGopherConfigClient {
  getEffectiveConfigCalls = 0;
  getEffectiveConfigError: Error | undefined;
  listMcpServersCalls = 0;
  listMcpServersError: Error | undefined;
  saveMcpServerError: Error | undefined;
  readonly saveMcpServerCalls: SaveMcpServerCall[] = [];
  readonly setMcpServerEnabledCalls: SetMcpServerEnabledCall[] = [];
  readonly deleteMcpServerCalls: string[] = [];
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
      replay_reasoning_content: true,
      config_sources: ["defaults", "project"]
    });
  }

  listMcpServers(): Promise<McpServersEvent> {
    this.listMcpServersCalls += 1;
    if (this.listMcpServersError) {
      return Promise.reject(this.listMcpServersError);
    }
    return Promise.resolve({
      version: 1,
      type: "mcp_servers",
      workspace_root: "/repo",
      servers: this.mcpServers
    });
  }

  saveMcpServer(serverName: string, server: McpServerPayload): Promise<McpServerSavedEvent> {
    this.saveMcpServerCalls.push({ serverName, server });
    if (this.saveMcpServerError) {
      return Promise.reject(this.saveMcpServerError);
    }
    return Promise.resolve({
      version: 1,
      type: "mcp_server_saved",
      workspace_root: "/repo",
      server_name: serverName,
      server
    });
  }

  setMcpServerEnabled(serverName: string, enabled: boolean): Promise<McpServerSavedEvent> {
    this.setMcpServerEnabledCalls.push({ serverName, enabled });
    return Promise.resolve({
      version: 1,
      type: "mcp_server_saved",
      workspace_root: "/repo",
      server_name: serverName,
      server: {
        enabled,
        transport: "stdio",
        command: "npx",
        args: ["@playwright/mcp@latest"]
      }
    });
  }

  deleteMcpServer(serverName: string): Promise<McpServerDeletedEvent> {
    this.deleteMcpServerCalls.push(serverName);
    return Promise.resolve({
      version: 1,
      type: "mcp_server_deleted",
      workspace_root: "/repo",
      server_name: serverName
    });
  }
}

class FakeConfigDialogs {
  readonly informationMessages: string[] = [];
  readonly errorMessages: string[] = [];
  readonly warningMessages: Array<{ message: string; options: unknown; items: string[] }> = [];
  readonly warningSelections: Array<string | undefined> = [];
  readonly quickPickCalls: Array<{ items: readonly CodeGopherQuickPickItem[]; options: unknown }> = [];
  readonly quickPickSelectionLabels: string[] = [];
  readonly inputValues: Array<string | undefined> = [];
  readonly inputBoxCalls: unknown[] = [];

  showInformationMessage(message: string): PromiseLike<string | undefined> {
    this.informationMessages.push(message);
    return Promise.resolve(undefined);
  }

  showErrorMessage(message: string): PromiseLike<string | undefined> {
    this.errorMessages.push(message);
    return Promise.resolve(undefined);
  }

  showWarningMessage(message: string, options: unknown, ...items: string[]): PromiseLike<string | undefined> {
    this.warningMessages.push({ message, options, items });
    return Promise.resolve(this.warningSelections.shift());
  }

  showQuickPick<T extends CodeGopherQuickPickItem>(
    items: readonly T[],
    options?: unknown
  ): PromiseLike<T | undefined> {
    this.quickPickCalls.push({ items, options });
    const label = this.quickPickSelectionLabels.shift();
    return Promise.resolve(label ? items.find((item) => item.label === label) : undefined);
  }

  showInputBox(options?: unknown): PromiseLike<string | undefined> {
    this.inputBoxCalls.push(options);
    return Promise.resolve(this.inputValues.shift());
  }
}
