import * as assert from "node:assert/strict";
import * as fs from "node:fs/promises";
import * as os from "node:os";
import * as path from "node:path";

import { CodeGopherClient } from "../../client";
import { CodeGopherConfigUiController } from "../../configUi";
import type {
  CodeGopherConfigDialogs,
  CodeGopherQuickPickItem,
} from "../../configUi";

suite("CodeGopher config UI e2e", () => {
  test("drives endpoint and MCP flows against cgopher --events", async function () {
    this.timeout(30_000);

    const workspaceRoot = await fs.mkdtemp(path.join(os.tmpdir(), "codegopher-vscode-workspace-"));
    const home = await fs.mkdtemp(path.join(os.tmpdir(), "codegopher-vscode-home-"));
    const originalHome = process.env.HOME;
    const originalOpenaiApiKey = process.env.OPENAI_API_KEY;
    process.env.HOME = home;
    process.env.OPENAI_API_KEY = "sk-codegopher-vscode-test";
    const client = new CodeGopherClient({
      cliPath: await resolveE2eCliPath(),
      workspaceRoot
    });
    const dialogs = new ScriptedConfigDialogs();
    const controller = new CodeGopherConfigUiController({
      clientProvider: () => client,
      dialogs
    });

    try {
      await controller.viewLlmEndpoint();
      assert.match(dialogs.informationMessages.pop() ?? "", /CodeGopher LLM Endpoint/);

      dialogs.selectQuickPick("$(add) Add stdio server");
      dialogs.addInputs("playwright", "npx", "[\"@playwright/mcp@latest\"]", "", "");
      await controller.manageMcpServers();
      let listed = await client.listMcpServers();
      assert.equal(listed.servers?.find((server) => server.name === "playwright")?.server.command, "npx");

      dialogs.selectQuickPick("$(check) playwright", "$(edit) Edit server");
      dialogs.addInputs("pnpm", "[\"exec\", \"playwright-mcp\"]", "", "");
      await controller.manageMcpServers();
      listed = await client.listMcpServers();
      assert.equal(listed.servers?.find((server) => server.name === "playwright")?.server.command, "pnpm");

      dialogs.selectQuickPick("$(check) playwright", "$(debug-pause) Disable server");
      await controller.manageMcpServers();
      listed = await client.listMcpServers();
      assert.equal(listed.servers?.find((server) => server.name === "playwright")?.server.enabled, false);

      dialogs.selectQuickPick("$(circle-slash) playwright", "$(debug-start) Enable server");
      await controller.manageMcpServers();
      listed = await client.listMcpServers();
      assert.equal(listed.servers?.find((server) => server.name === "playwright")?.server.enabled, true);

      dialogs.selectQuickPick("$(check) playwright", "$(trash) Remove server");
      dialogs.addWarnings("Remove");
      await controller.manageMcpServers();
      listed = await client.listMcpServers();
      assert.equal(listed.servers?.some((server) => server.name === "playwright"), false);

      dialogs.selectQuickPick("$(add) Add SSE server");
      dialogs.addInputs("docs", "https://mcp.example.test/sse", "7", "400");
      await controller.manageMcpServers();
      listed = await client.listMcpServers();
      const docs = listed.servers?.find((server) => server.name === "docs");
      assert.equal(docs?.server.transport, "sse");
      assert.equal(docs?.server.timeout_seconds, 7);
      assert.equal(docs?.server.sse_read_timeout_seconds, 400);

      await client.saveMcpServer("secure", {
        enabled: true,
        transport: "sse",
        url: "https://mcp.example.test/sse",
        headers: { Authorization: "Bearer raw-token" }
      });
      dialogs.selectQuickPick("$(check) secure", "$(edit) Edit server");
      await controller.manageMcpServers();
      const secretError = dialogs.errorMessages.pop() ?? "";
      assert.match(secretError, /headers_env|headers/);
      assert.doesNotMatch(secretError, /raw-token/);
    } finally {
      await client.shutdown().catch(() => undefined);
      if (originalHome === undefined) {
        delete process.env.HOME;
      } else {
        process.env.HOME = originalHome;
      }
      if (originalOpenaiApiKey === undefined) {
        delete process.env.OPENAI_API_KEY;
      } else {
        process.env.OPENAI_API_KEY = originalOpenaiApiKey;
      }
      await fs.rm(workspaceRoot, { recursive: true, force: true });
      await fs.rm(home, { recursive: true, force: true });
    }
  });
});

class ScriptedConfigDialogs implements CodeGopherConfigDialogs {
  readonly informationMessages: string[] = [];
  readonly errorMessages: string[] = [];
  readonly warningMessages: string[] = [];
  private readonly quickPickSelectionLabels: string[] = [];
  private readonly inputValues: Array<string | undefined> = [];
  private readonly warningSelections: Array<string | undefined> = [];

  selectQuickPick(...labels: string[]): void {
    this.quickPickSelectionLabels.push(...labels);
  }

  addInputs(...values: Array<string | undefined>): void {
    this.inputValues.push(...values);
  }

  addWarnings(...values: Array<string | undefined>): void {
    this.warningSelections.push(...values);
  }

  showInformationMessage(message: string): PromiseLike<string | undefined> {
    this.informationMessages.push(message);
    return Promise.resolve(undefined);
  }

  showErrorMessage(message: string): PromiseLike<string | undefined> {
    this.errorMessages.push(message);
    return Promise.resolve(undefined);
  }

  showWarningMessage(message: string): PromiseLike<string | undefined> {
    this.warningMessages.push(message);
    return Promise.resolve(this.warningSelections.shift());
  }

  showQuickPick<T extends CodeGopherQuickPickItem>(items: readonly T[]): PromiseLike<T | undefined> {
    const label = this.quickPickSelectionLabels.shift();
    return Promise.resolve(label ? items.find((item) => item.label === label) : undefined);
  }

  showInputBox(): PromiseLike<string | undefined> {
    return Promise.resolve(this.inputValues.shift());
  }
}

async function resolveE2eCliPath(): Promise<string> {
  if (process.env.CODEGOPHER_E2E_CLI_PATH) {
    return process.env.CODEGOPHER_E2E_CLI_PATH;
  }

  const repoRoot = path.resolve(__dirname, "../../../../..");
  const candidates = [
    path.join(repoRoot, ".venv", "bin", "cgopher"),
    path.join(repoRoot, ".venv", "Scripts", "cgopher.exe")
  ];
  for (const candidate of candidates) {
    try {
      await fs.access(candidate);
      return candidate;
    } catch {
      // Try the next candidate.
    }
  }
  return "cgopher";
}
