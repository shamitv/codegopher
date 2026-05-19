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

  startTurn(prompt: string, options?: unknown): Promise<TurnCompleteEvent> {
    this.startCalls.push({ prompt, options });
    return new Promise<TurnCompleteEvent>((resolve) => {
      this.resolveTurn = resolve;
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
}

class FakeChatResponseStream {
  readonly markdownParts: string[] = [];

  asChatStream(): vscode.ChatResponseStream {
    return {
      markdown: (value) => {
        this.markdownParts.push(value.toString());
      },
      anchor: () => undefined,
      button: () => undefined,
      filetree: () => undefined,
      progress: () => undefined,
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
