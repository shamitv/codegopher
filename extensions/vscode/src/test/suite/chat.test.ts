import * as assert from "node:assert/strict";

import type * as vscode from "vscode";

import { CodeGopherChatController, type CodeGopherChatClient } from "../../chat";
import type { Disposable } from "../../client";
import type { ProtocolEvent, TurnCompleteEvent } from "../../protocol";

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
});

interface StartCall {
  prompt: string;
  options: unknown;
}

class FakeChatClient implements CodeGopherChatClient {
  readonly isRunning = true;
  readonly startCalls: StartCall[] = [];
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

  onEvent(listener: (event: ProtocolEvent) => void): Disposable {
    this.listeners.add(listener);
    return {
      dispose: () => {
        this.listeners.delete(listener);
      }
    };
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

  asChatStream(): vscode.ChatResponseStream {
    return {
      markdown: (value) => {
        this.markdownParts.push(value.toString());
      },
      anchor: () => undefined,
      button: () => undefined,
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

function fakeCancellationToken(): vscode.CancellationToken {
  return {
    isCancellationRequested: false,
    onCancellationRequested: () => ({ dispose: () => undefined })
  };
}
