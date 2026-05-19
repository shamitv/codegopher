import * as assert from "node:assert/strict";

import type * as vscode from "vscode";

import {
  approvalApproveCommandId,
  approvalDenyCommandId,
  CodeGopherChatController,
  defaultApprovalDenialReason,
  type CodeGopherChatClient
} from "../../chat";
import type { Disposable } from "../../client";
import type { ProtocolEvent, SessionStartedEvent, TurnCompleteEvent } from "../../protocol";

suite("CodeGopher chat controller", () => {
  test("streams text_delta events into chat markdown", async () => {
    const fakeClient = new FakeChatClient();
    const stream = new FakeChatResponseStream();
    const controller = new CodeGopherChatController({
      outputChannel: new FakeOutputChannel(),
      clientFactory: () => fakeClient,
      turnIdFactory: () => "turn-chat"
    });

    const resultPromise = controller.handleRequest(
      fakeRequest("explain this"),
      fakeContext(),
      stream.asChatStream(),
      fakeCancellationToken()
    );

    assert.deepEqual(fakeClient.startCalls, [
      {
        prompt: "explain this",
        options: {
          turnId: "turn-chat",
          selectedFile: null,
          editorMetadata: {}
        }
      }
    ]);

    fakeClient.emit({
      version: 1,
      type: "text_delta",
      turn_id: "turn-chat",
      content: "Hello "
    });
    fakeClient.emit({
      version: 1,
      type: "text_delta",
      turn_id: "other-turn",
      content: "ignored"
    });
    fakeClient.emit({
      version: 1,
      type: "text_delta",
      turn_id: "turn-chat",
      content: "there"
    });
    fakeClient.completeTurn({
      version: 1,
      type: "turn_complete",
      turn_id: "turn-chat",
      final_text: "Hello there"
    });

    assert.deepEqual(await resultPromise, {
      metadata: {
        command: null,
        participant: "codegopher",
        turnId: "turn-chat"
      }
    });
    assert.deepEqual(stream.markdownParts, ["Hello ", "there"]);

    fakeClient.emit({
      version: 1,
      type: "text_delta",
      turn_id: "turn-chat",
      content: " after dispose"
    });
    assert.deepEqual(stream.markdownParts, ["Hello ", "there"]);
  });

  test("renders tool call and result events as compact progress", async () => {
    const fakeClient = new FakeChatClient();
    const stream = new FakeChatResponseStream();
    const controller = new CodeGopherChatController({
      outputChannel: new FakeOutputChannel(),
      clientFactory: () => fakeClient,
      turnIdFactory: () => "turn-tools"
    });

    const resultPromise = controller.handleRequest(
      fakeRequest("read"),
      fakeContext(),
      stream.asChatStream(),
      fakeCancellationToken()
    );

    fakeClient.emit({
      version: 1,
      type: "tool_call",
      turn_id: "turn-tools",
      tool_id: "tool-1",
      tool_name: "read_file",
      arguments_summary: "{\"path\":\"README.md\"}"
    });
    fakeClient.emit({
      version: 1,
      type: "tool_result",
      turn_id: "turn-tools",
      tool_id: "tool-1",
      is_error: false,
      result_summary: `${"line ".repeat(60)}done`
    });
    fakeClient.emit({
      version: 1,
      type: "tool_result",
      turn_id: "other-turn",
      tool_id: "tool-1",
      result_summary: "ignored"
    });
    fakeClient.completeTurn({
      version: 1,
      type: "turn_complete",
      turn_id: "turn-tools"
    });

    await resultPromise;

    assert.deepEqual(stream.progressParts[0], "Calling read_file: {\"path\":\"README.md\"}");
    assert.equal(stream.progressParts.length, 2);
    assert.match(stream.progressParts[1], /^read_file completed: line line/);
    assert.equal(stream.progressParts[1].length, "read_file completed: ".length + 160);
    assert.match(stream.progressParts[1], /\.\.\.$/);
  });

  test("renders approval requests with approve and deny buttons", async () => {
    const fakeClient = new FakeChatClient();
    const stream = new FakeChatResponseStream();
    const controller = new CodeGopherChatController({
      outputChannel: new FakeOutputChannel(),
      clientFactory: () => fakeClient,
      turnIdFactory: () => "turn-approval"
    });

    const resultPromise = controller.handleRequest(
      fakeRequest("write"),
      fakeContext(),
      stream.asChatStream(),
      fakeCancellationToken()
    );

    fakeClient.emit({
      version: 1,
      type: "approval_request",
      turn_id: "turn-approval",
      approval_id: "approval-1",
      tool_name: "write_file",
      arguments_summary: "{\"path\":\"new.txt\"}",
      raw_arguments: { path: "new.txt" }
    });
    fakeClient.completeTurn({
      version: 1,
      type: "turn_complete",
      turn_id: "turn-approval"
    });

    await resultPromise;

    assert.deepEqual(stream.progressParts, ["Approval required for write_file: {\"path\":\"new.txt\"}"]);
    assert.deepEqual(stream.buttonParts, [
      {
        command: approvalApproveCommandId,
        title: "Approve",
        arguments: ["approval-1"]
      },
      {
        command: approvalDenyCommandId,
        title: "Deny",
        arguments: ["approval-1"]
      }
    ]);
  });

  test("routes approve decisions to approval_response", async () => {
    const fakeClient = new FakeChatClient();
    const stream = new FakeChatResponseStream();
    const controller = new CodeGopherChatController({
      outputChannel: new FakeOutputChannel(),
      clientFactory: () => fakeClient,
      turnIdFactory: () => "turn-approve"
    });

    const resultPromise = controller.handleRequest(
      fakeRequest("write"),
      fakeContext(),
      stream.asChatStream(),
      fakeCancellationToken()
    );

    fakeClient.emit({
      version: 1,
      type: "approval_request",
      turn_id: "turn-approve",
      approval_id: "approval-approve",
      tool_name: "write_file"
    });

    controller.approveApproval("approval-approve");

    assert.deepEqual(fakeClient.approvalCalls, [
      {
        approvalId: "approval-approve",
        approved: true,
        reason: undefined
      }
    ]);

    fakeClient.completeTurn({
      version: 1,
      type: "turn_complete",
      turn_id: "turn-approve"
    });
    await resultPromise;
  });

  test("routes deny decisions to approval_response with a default reason", async () => {
    const fakeClient = new FakeChatClient();
    const stream = new FakeChatResponseStream();
    const controller = new CodeGopherChatController({
      outputChannel: new FakeOutputChannel(),
      clientFactory: () => fakeClient,
      turnIdFactory: () => "turn-deny"
    });

    const resultPromise = controller.handleRequest(
      fakeRequest("write"),
      fakeContext(),
      stream.asChatStream(),
      fakeCancellationToken()
    );

    fakeClient.emit({
      version: 1,
      type: "approval_request",
      turn_id: "turn-deny",
      approval_id: "approval-deny",
      tool_name: "write_file"
    });

    controller.denyApproval("approval-deny");

    assert.deepEqual(fakeClient.approvalCalls, [
      {
        approvalId: "approval-deny",
        approved: false,
        reason: defaultApprovalDenialReason
      }
    ]);

    fakeClient.completeTurn({
      version: 1,
      type: "turn_complete",
      turn_id: "turn-deny"
    });
    await resultPromise;
  });

  test("prevents duplicate approval decisions for the same approval id", async () => {
    const fakeClient = new FakeChatClient();
    const stream = new FakeChatResponseStream();
    const outputChannel = new FakeOutputChannel();
    const controller = new CodeGopherChatController({
      outputChannel,
      clientFactory: () => fakeClient,
      turnIdFactory: () => "turn-duplicate-approval"
    });

    const resultPromise = controller.handleRequest(
      fakeRequest("write"),
      fakeContext(),
      stream.asChatStream(),
      fakeCancellationToken()
    );

    fakeClient.emit({
      version: 1,
      type: "approval_request",
      turn_id: "turn-duplicate-approval",
      approval_id: "approval-duplicate",
      tool_name: "write_file"
    });

    controller.approveApproval("approval-duplicate");
    controller.approveApproval("approval-duplicate");
    controller.denyApproval("approval-duplicate");

    assert.deepEqual(fakeClient.approvalCalls, [
      {
        approvalId: "approval-duplicate",
        approved: true,
        reason: undefined
      }
    ]);
    assert.equal(
      outputChannel.lines.filter((line) =>
        line.includes("CodeGopher approval ignored; no pending approval for approval-duplicate.")
      ).length,
      2
    );

    fakeClient.completeTurn({
      version: 1,
      type: "turn_complete",
      turn_id: "turn-duplicate-approval"
    });
    await resultPromise;
  });

  test("sends cancel_turn when VS Code cancels the chat request", async () => {
    const fakeClient = new FakeChatClient();
    const stream = new FakeChatResponseStream();
    const outputChannel = new FakeOutputChannel();
    const token = fakeCancellationToken();
    const controller = new CodeGopherChatController({
      outputChannel,
      clientFactory: () => fakeClient,
      turnIdFactory: () => "turn-cancel"
    });

    const resultPromise = controller.handleRequest(fakeRequest("stop"), fakeContext(), stream.asChatStream(), token);

    token.cancel();
    token.cancel();

    assert.deepEqual(fakeClient.cancelCalls, ["turn-cancel"]);
    assert.deepEqual(outputChannel.lines, ["CodeGopher cancellation requested for turn-cancel."]);

    fakeClient.emit({
      version: 1,
      type: "error",
      turn_id: "turn-cancel",
      code: "turn_cancelled",
      message: "Turn cancelled"
    });
    fakeClient.failTurn(new Error("turn_cancelled: Turn cancelled"));

    assert.deepEqual(await resultPromise, {
      errorDetails: {
        message: "turn_cancelled: Turn cancelled"
      },
      metadata: {
        command: null,
        participant: "codegopher",
        turnId: "turn-cancel"
      }
    });
  });

  test("returns one user-facing error when an error event rejects the turn", async () => {
    const fakeClient = new FakeChatClient();
    const stream = new FakeChatResponseStream();
    const controller = new CodeGopherChatController({
      outputChannel: new FakeOutputChannel(),
      clientFactory: () => fakeClient,
      turnIdFactory: () => "turn-error"
    });

    const resultPromise = controller.handleRequest(
      fakeRequest("fail"),
      fakeContext(),
      stream.asChatStream(),
      fakeCancellationToken()
    );

    fakeClient.emit({
      version: 1,
      type: "error",
      turn_id: "turn-error",
      code: "provider_error",
      message: "provider failed"
    });
    fakeClient.failTurn(new Error("provider_error: provider failed"));

    assert.deepEqual(await resultPromise, {
      errorDetails: {
        message: "provider_error: provider failed"
      },
      metadata: {
        command: null,
        participant: "codegopher",
        turnId: "turn-error"
      }
    });
    assert.deepEqual(stream.markdownParts, ["CodeGopher error: provider_error: provider failed"]);
  });

  test("renders client failures without a protocol error event", async () => {
    const fakeClient = new FakeChatClient();
    const stream = new FakeChatResponseStream();
    const controller = new CodeGopherChatController({
      outputChannel: new FakeOutputChannel(),
      clientFactory: () => fakeClient,
      turnIdFactory: () => "turn-client-error"
    });

    const resultPromise = controller.handleRequest(
      fakeRequest("fail before event"),
      fakeContext(),
      stream.asChatStream(),
      fakeCancellationToken()
    );

    fakeClient.failTurn(new Error("CodeGopher subprocess exited."));

    assert.deepEqual(await resultPromise, {
      errorDetails: {
        message: "CodeGopher subprocess exited."
      },
      metadata: {
        command: null,
        participant: "codegopher",
        turnId: "turn-client-error"
      }
    });
    assert.deepEqual(stream.markdownParts, ["CodeGopher error: CodeGopher subprocess exited."]);
  });

  test("hides reasoning deltas from chat while logging content-free progress", async () => {
    const fakeClient = new FakeChatClient();
    const stream = new FakeChatResponseStream();
    const outputChannel = new FakeOutputChannel();
    const controller = new CodeGopherChatController({
      outputChannel,
      clientFactory: () => fakeClient,
      turnIdFactory: () => "turn-reasoning"
    });

    const resultPromise = controller.handleRequest(
      fakeRequest("think"),
      fakeContext(),
      stream.asChatStream(),
      fakeCancellationToken()
    );

    fakeClient.emit({
      version: 1,
      type: "reasoning_delta",
      turn_id: "turn-reasoning",
      content: "private chain of thought"
    });
    fakeClient.emit({
      version: 1,
      type: "text_delta",
      turn_id: "turn-reasoning",
      content: "public answer"
    });
    fakeClient.completeTurn({
      version: 1,
      type: "turn_complete",
      turn_id: "turn-reasoning",
      final_text: "public answer"
    });

    await resultPromise;

    assert.deepEqual(stream.markdownParts, ["public answer"]);
    assert.deepEqual(stream.progressParts, []);
    assert.deepEqual(outputChannel.lines, ["CodeGopher reasoning update for turn-reasoning."]);
    assert.ok(!outputChannel.lines.join("\n").includes("private chain of thought"));
  });

  test("renders help without starting an agent turn", async () => {
    const fakeClient = new FakeChatClient();
    const stream = new FakeChatResponseStream();
    const controller = new CodeGopherChatController({
      outputChannel: new FakeOutputChannel(),
      clientFactory: () => fakeClient
    });

    const result = await controller.handleRequest(
      fakeRequest("", "help"),
      fakeContext(),
      stream.asChatStream(),
      fakeCancellationToken()
    );

    assert.deepEqual(result, {
      metadata: {
        command: "help",
        participant: "codegopher"
      }
    });
    assert.equal(fakeClient.startCalls.length, 0);
    assert.match(stream.markdownParts[0], /@codegopher/);
    assert.match(stream.markdownParts[0], /\/status/);
  });

  test("renders status from settings and known session state", async () => {
    const fakeClient = new FakeChatClient();
    fakeClient.sessionStarted = {
      version: 1,
      type: "session_started",
      session_id: "session-1",
      cwd: "/repo",
      provider: "openai",
      model: "gpt-session",
      approval_mode: "review"
    };
    const stream = new FakeChatResponseStream();
    const controller = new CodeGopherChatController({
      outputChannel: new FakeOutputChannel(),
      clientFactory: () => fakeClient,
      settingsProvider: () => ({
        cliPath: "/bin/cgopher",
        provider: "configured-provider",
        model: "configured-model",
        baseUrl: "",
        apiFamily: "",
        approvalMode: "",
        traceProtocol: true
      }),
      workspaceRootProvider: () => "/repo",
      turnIdFactory: () => "turn-before-status"
    });

    const turn = controller.handleRequest(
      fakeRequest("hello"),
      fakeContext(),
      new FakeChatResponseStream().asChatStream(),
      fakeCancellationToken()
    );
    fakeClient.completeTurn({
      version: 1,
      type: "turn_complete",
      turn_id: "turn-before-status"
    });
    await turn;

    const result = await controller.handleRequest(
      fakeRequest("", "status"),
      fakeContext(),
      stream.asChatStream(),
      fakeCancellationToken()
    );

    assert.deepEqual(result, {
      metadata: {
        command: "status",
        participant: "codegopher"
      }
    });
    assert.equal(fakeClient.startCalls.length, 1);
    assert.match(stream.markdownParts[0], /CLI: `\/bin\/cgopher`/);
    assert.match(stream.markdownParts[0], /Workspace: `\/repo`/);
    assert.match(stream.markdownParts[0], /Subprocess: running/);
    assert.match(stream.markdownParts[0], /Provider: openai/);
    assert.match(stream.markdownParts[0], /Model: gpt-session/);
    assert.match(stream.markdownParts[0], /Approval mode: review/);
    assert.match(stream.markdownParts[0], /Protocol trace: enabled/);
  });

  test("restarts from chat command", async () => {
    const fakeClient = new FakeChatClient();
    const stream = new FakeChatResponseStream();
    const controller = new CodeGopherChatController({
      outputChannel: new FakeOutputChannel(),
      clientFactory: () => fakeClient
    });

    const result = await controller.handleRequest(
      fakeRequest("", "restart"),
      fakeContext(),
      stream.asChatStream(),
      fakeCancellationToken()
    );

    assert.equal(fakeClient.restartCalls, 1);
    assert.deepEqual(result, {
      metadata: {
        command: "restart",
        participant: "codegopher"
      }
    });
    assert.deepEqual(stream.progressParts, ["Restarting CodeGopher..."]);
    assert.deepEqual(stream.markdownParts, ["CodeGopher restarted with openai / gpt-test."]);
  });

  test("returns chat restart failures as error results", async () => {
    const fakeClient = new FakeChatClient();
    fakeClient.restartError = new Error("restart failed");
    const stream = new FakeChatResponseStream();
    const controller = new CodeGopherChatController({
      outputChannel: new FakeOutputChannel(),
      clientFactory: () => fakeClient
    });

    const result = await controller.handleRequest(
      fakeRequest("", "restart"),
      fakeContext(),
      stream.asChatStream(),
      fakeCancellationToken()
    );

    assert.equal(fakeClient.restartCalls, 1);
    assert.deepEqual(result, {
      errorDetails: {
        message: "restart failed"
      },
      metadata: {
        command: "restart",
        participant: "codegopher"
      }
    });
    assert.deepEqual(stream.markdownParts, ["CodeGopher error: restart failed"]);
  });

  test("restarts from command palette path", async () => {
    const fakeClient = new FakeChatClient();
    const controller = new CodeGopherChatController({
      outputChannel: new FakeOutputChannel(),
      clientFactory: () => fakeClient
    });

    await controller.restart();

    assert.equal(fakeClient.restartCalls, 1);
  });
});

interface StartCall {
  prompt: string;
  options: unknown;
}

interface ApprovalCall {
  approvalId: string;
  approved: boolean;
  reason?: string | null;
}

class FakeChatClient implements CodeGopherChatClient {
  readonly isRunning = true;
  sessionStarted: SessionStartedEvent | undefined = undefined;
  readonly startCalls: StartCall[] = [];
  readonly approvalCalls: ApprovalCall[] = [];
  readonly cancelCalls: string[] = [];
  restartCalls = 0;
  restartError: Error | undefined;
  private readonly listeners = new Set<(event: ProtocolEvent) => void>();
  private resolveTurn: ((event: TurnCompleteEvent) => void) | undefined;
  private rejectTurn: ((error: Error) => void) | undefined;

  startTurn(prompt: string, options?: unknown): Promise<TurnCompleteEvent> {
    this.startCalls.push({ prompt, options });
    return new Promise<TurnCompleteEvent>((resolve, reject) => {
      this.resolveTurn = resolve;
      this.rejectTurn = reject;
    });
  }

  submitApproval(approvalId: string, approved: boolean, reason?: string | null): void {
    this.approvalCalls.push({ approvalId, approved, reason });
  }

  cancelTurn(turnId: string): void {
    this.cancelCalls.push(turnId);
  }

  onEvent(listener: (event: ProtocolEvent) => void): Disposable {
    this.listeners.add(listener);
    return {
      dispose: () => {
        this.listeners.delete(listener);
      }
    };
  }

  restart(): Promise<SessionStartedEvent> {
    this.restartCalls += 1;
    if (this.restartError) {
      return Promise.reject(this.restartError);
    }
    this.sessionStarted = {
      version: 1,
      type: "session_started",
      session_id: "session-restart",
      cwd: "/repo",
      provider: "openai",
      model: "gpt-test",
      approval_mode: "review"
    };
    return Promise.resolve(this.sessionStarted);
  }

  emit(event: ProtocolEvent): void {
    for (const listener of this.listeners) {
      listener(event);
    }
  }

  completeTurn(event: TurnCompleteEvent): void {
    this.resolveTurn?.(event);
  }

  failTurn(error: Error): void {
    this.rejectTurn?.(error);
  }
}

class FakeChatResponseStream {
  readonly markdownParts: string[] = [];
  readonly progressParts: string[] = [];
  readonly buttonParts: vscode.Command[] = [];

  asChatStream(): vscode.ChatResponseStream {
    return {
      markdown: (value) => {
        this.markdownParts.push(value.toString());
      },
      anchor: () => undefined,
      button: (value) => {
        this.buttonParts.push(value);
      },
      filetree: () => undefined,
      progress: (value) => {
        this.progressParts.push(value);
      },
      reference: () => undefined,
      push: () => undefined
    };
  }
}

class FakeOutputChannel implements vscode.OutputChannel {
  readonly name = "CodeGopher Test";
  readonly lines: string[] = [];
  append(value: string): void {
    this.lines.push(value);
  }
  appendLine(value: string): void {
    this.lines.push(value);
  }
  replace(value: string): void {
    this.lines.splice(0, this.lines.length, value);
  }
  clear(): void {
    this.lines.splice(0);
  }
  show(): void {
    return undefined;
  }
  hide(): void {
    return undefined;
  }
  dispose(): void {
    return undefined;
  }
}

function fakeRequest(prompt: string, command?: string): vscode.ChatRequest {
  return {
    prompt,
    command,
    references: [],
    toolReferences: [],
    toolInvocationToken: undefined as never,
    model: undefined as never
  };
}

function fakeContext(): vscode.ChatContext {
  return {
    history: []
  };
}

function fakeCancellationToken(): FakeCancellationToken {
  return new FakeCancellationToken();
}

class FakeCancellationToken implements vscode.CancellationToken {
  isCancellationRequested = false;
  private readonly listeners = new Set<() => void>();

  onCancellationRequested(
    listener: (event: unknown) => unknown,
    thisArgs?: unknown,
    disposables?: vscode.Disposable[]
  ): vscode.Disposable {
    const wrapped = () => {
      listener.call(thisArgs, undefined);
    };
    this.listeners.add(wrapped);
    const disposable = {
      dispose: () => {
        this.listeners.delete(wrapped);
      }
    };
    disposables?.push(disposable);
    return disposable;
  }

  cancel(): void {
    if (this.isCancellationRequested) {
      return;
    }
    this.isCancellationRequested = true;
    for (const listener of [...this.listeners]) {
      listener();
    }
  }
}
