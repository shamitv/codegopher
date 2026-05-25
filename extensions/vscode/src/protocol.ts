export const protocolVersion = 1;
export const redactedProtocolValue = "[redacted]";

export type ProtocolVersion = typeof protocolVersion;
export type ApprovalMode = "review" | "auto" | "yolo";
export type ApiFamily = "chat_completions" | "responses";
export type McpTransport = "stdio" | "sse";

export interface ProtocolBase {
  version: ProtocolVersion;
  type: string;
  session_id?: string | null;
  turn_id?: string | null;
}

export interface StartTurnCommand extends ProtocolBase {
  type: "start_turn";
  prompt: string;
  workspace_root: string;
  selected_file?: string | null;
  editor_metadata?: Record<string, unknown>;
  overrides?: Record<string, unknown>;
}

export interface ApprovalResponseCommand extends ProtocolBase {
  type: "approval_response";
  approval_id: string;
  approved: boolean;
  reason?: string | null;
}

export interface CancelTurnCommand extends ProtocolBase {
  type: "cancel_turn";
  turn_id: string;
}

export interface ShutdownCommand extends ProtocolBase {
  type: "shutdown";
}

export interface GetEffectiveConfigCommand extends ProtocolBase {
  type: "get_effective_config";
  workspace_root: string;
}

export interface ListMcpServersCommand extends ProtocolBase {
  type: "list_mcp_servers";
  workspace_root: string;
}

export interface McpServerPayload {
  enabled?: boolean;
  transport?: McpTransport;
  command?: string | null;
  args?: string[];
  env?: Record<string, string>;
  cwd?: string | null;
  startup_timeout_seconds?: number;
  url?: string | null;
  headers?: Record<string, string>;
  headers_env?: Record<string, string>;
  timeout_seconds?: number;
  sse_read_timeout_seconds?: number;
}

export interface SaveMcpServerCommand extends ProtocolBase {
  type: "save_mcp_server";
  workspace_root: string;
  server_name: string;
  server: McpServerPayload;
}

export interface SetMcpServerEnabledCommand extends ProtocolBase {
  type: "set_mcp_server_enabled";
  workspace_root: string;
  server_name: string;
  enabled: boolean;
}

export interface DeleteMcpServerCommand extends ProtocolBase {
  type: "delete_mcp_server";
  workspace_root: string;
  server_name: string;
}

export type ProtocolCommand =
  | StartTurnCommand
  | ApprovalResponseCommand
  | CancelTurnCommand
  | ShutdownCommand
  | GetEffectiveConfigCommand
  | ListMcpServersCommand
  | SaveMcpServerCommand
  | SetMcpServerEnabledCommand
  | DeleteMcpServerCommand;

export interface SessionStartedEvent extends ProtocolBase {
  type: "session_started";
  session_id: string;
  cwd: string;
  provider: string;
  model: string;
  approval_mode: ApprovalMode;
}

export interface TurnStartedEvent extends ProtocolBase {
  type: "turn_started";
  session_id: string;
  turn_id: string;
  cwd: string;
}

export interface TextDeltaEvent extends ProtocolBase {
  type: "text_delta";
  turn_id: string;
  content: string;
}

export interface ReasoningDeltaEvent extends ProtocolBase {
  type: "reasoning_delta";
  turn_id: string;
  content: string;
}

export interface ToolCallEvent extends ProtocolBase {
  type: "tool_call";
  turn_id: string;
  tool_id: string;
  tool_name: string;
  arguments_summary?: string;
}

export interface ApprovalRequestEvent extends ProtocolBase {
  type: "approval_request";
  turn_id: string;
  approval_id: string;
  tool_name: string;
  arguments_summary?: string;
  raw_arguments?: Record<string, unknown> | null;
}

export interface ToolResultEvent extends ProtocolBase {
  type: "tool_result";
  turn_id: string;
  tool_id: string;
  is_error?: boolean;
  result_summary?: string;
}

export interface ErrorEvent extends ProtocolBase {
  type: "error";
  code: string;
  message: string;
}

export interface TurnCompleteEvent extends ProtocolBase {
  type: "turn_complete";
  turn_id: string;
  final_text?: string;
  tool_count?: number;
  approval_count?: number;
  iteration_count?: number;
}

export interface ConfigSnapshotEvent extends ProtocolBase {
  type: "config_snapshot";
  workspace_root: string;
  provider: string;
  model: string;
  api_family: ApiFamily;
  base_url?: string | null;
  replay_reasoning_content?: boolean;
  config_sources?: string[];
}

export interface McpServerSnapshotPayload {
  name: string;
  source?: string | null;
  server: McpServerPayload;
}

export interface McpServersEvent extends ProtocolBase {
  type: "mcp_servers";
  workspace_root: string;
  servers?: McpServerSnapshotPayload[];
}

export interface McpServerSavedEvent extends ProtocolBase {
  type: "mcp_server_saved";
  workspace_root: string;
  server_name: string;
  server: McpServerPayload;
}

export interface McpServerDeletedEvent extends ProtocolBase {
  type: "mcp_server_deleted";
  workspace_root: string;
  server_name: string;
}

export type ProtocolEvent =
  | SessionStartedEvent
  | TurnStartedEvent
  | TextDeltaEvent
  | ReasoningDeltaEvent
  | ToolCallEvent
  | ApprovalRequestEvent
  | ToolResultEvent
  | ErrorEvent
  | TurnCompleteEvent
  | ConfigSnapshotEvent
  | McpServersEvent
  | McpServerSavedEvent
  | McpServerDeletedEvent;

export type ProtocolMessage = ProtocolCommand | ProtocolEvent;

export const protocolTypes = [
  "start_turn",
  "approval_response",
  "cancel_turn",
  "shutdown",
  "get_effective_config",
  "list_mcp_servers",
  "save_mcp_server",
  "set_mcp_server_enabled",
  "delete_mcp_server",
  "session_started",
  "turn_started",
  "text_delta",
  "reasoning_delta",
  "tool_call",
  "approval_request",
  "tool_result",
  "error",
  "turn_complete",
  "config_snapshot",
  "mcp_servers",
  "mcp_server_saved",
  "mcp_server_deleted"
] as const;

type ProtocolType = (typeof protocolTypes)[number];

export const protocolEventTypes = [
  "session_started",
  "turn_started",
  "text_delta",
  "reasoning_delta",
  "tool_call",
  "approval_request",
  "tool_result",
  "error",
  "turn_complete",
  "config_snapshot",
  "mcp_servers",
  "mcp_server_saved",
  "mcp_server_deleted"
] as const;

const protocolTypeSet = new Set<string>(protocolTypes);
const protocolEventTypeSet = new Set<string>(protocolEventTypes);
const sensitiveContainerKeys = new Set(["env", "headers", "headers_env"]);
const sensitiveKeyParts = [
  "api_key",
  "apikey",
  "authorization",
  "bearer",
  "credential",
  "password",
  "passwd",
  "secret",
  "token"
] as const;

export class ProtocolParseError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ProtocolParseError";
  }
}

export function encodeProtocolMessage(message: ProtocolMessage): string {
  return `${JSON.stringify({ ...message, version: protocolVersion })}\n`;
}

export function decodeProtocolLine(line: string): ProtocolMessage {
  const payload = line.trim();
  if (!payload) {
    throw new ProtocolParseError("Empty protocol line");
  }

  let value: unknown;
  try {
    value = JSON.parse(payload);
  } catch (error) {
    const detail = error instanceof Error ? error.message : "invalid JSON";
    throw new ProtocolParseError(`Malformed protocol JSON: ${detail}`);
  }

  const message = asRecord(value, "Protocol payload must be a JSON object");
  if (message.version !== protocolVersion) {
    if (!Object.hasOwn(message, "version")) {
      throw new ProtocolParseError("Protocol payload missing version");
    }
    throw new ProtocolParseError(`Unsupported protocol version: ${String(message.version)}`);
  }

  const type = message.type;
  if (typeof type !== "string") {
    if (!Object.hasOwn(message, "type")) {
      throw new ProtocolParseError("Protocol payload missing type");
    }
    throw new ProtocolParseError("Protocol payload type must be a string");
  }
  if (!protocolTypeSet.has(type)) {
    throw new ProtocolParseError(`Unknown protocol type: ${type}`);
  }

  validateMessage(type as ProtocolType, message);
  return message as unknown as ProtocolMessage;
}

export class JsonlProtocolParser {
  private buffer = "";

  push(chunk: Buffer | string): ProtocolMessage[] {
    this.buffer += typeof chunk === "string" ? chunk : chunk.toString("utf8");
    const messages: ProtocolMessage[] = [];

    for (;;) {
      const newlineIndex = this.buffer.indexOf("\n");
      if (newlineIndex === -1) {
        break;
      }
      const line = stripTrailingCarriageReturn(this.buffer.slice(0, newlineIndex));
      this.buffer = this.buffer.slice(newlineIndex + 1);
      messages.push(decodeProtocolLine(line));
    }

    return messages;
  }

  flush(): ProtocolMessage[] {
    if (!this.buffer) {
      return [];
    }
    const line = stripTrailingCarriageReturn(this.buffer);
    this.buffer = "";
    return [decodeProtocolLine(line)];
  }

  clear(): void {
    this.buffer = "";
  }
}

export function isProtocolEvent(message: ProtocolMessage): message is ProtocolEvent {
  return protocolEventTypeSet.has(message.type);
}

export function redactProtocolValue(value: unknown): unknown {
  if (Array.isArray(value)) {
    return value.map((item) => redactProtocolValue(item));
  }
  if (!isRecord(value)) {
    return value;
  }

  const redacted: Record<string, unknown> = {};
  for (const [key, item] of Object.entries(value)) {
    const normalized = key.toLowerCase().replaceAll("-", "_");
    if (sensitiveContainerKeys.has(normalized)) {
      redacted[key] = redactContainerValues(item);
    } else if (sensitiveKeyParts.some((part) => normalized.includes(part))) {
      redacted[key] = redactedProtocolValue;
    } else {
      redacted[key] = redactProtocolValue(item);
    }
  }
  return redacted;
}

function redactContainerValues(value: unknown): unknown {
  if (Array.isArray(value)) {
    return value.map((item) => redactContainerValues(item));
  }
  if (!isRecord(value)) {
    return redactedProtocolValue;
  }
  return Object.fromEntries(Object.entries(value).map(([key, item]) => [key, redactContainerValues(item)]));
}

function validateMessage(type: ProtocolType, message: Record<string, unknown>): void {
  switch (type) {
    case "start_turn":
      requireString(message, "prompt");
      requireString(message, "workspace_root");
      optionalRecord(message, "editor_metadata");
      optionalRecord(message, "overrides");
      optionalStringOrNull(message, "selected_file");
      break;
    case "approval_response":
      requireString(message, "approval_id");
      requireBoolean(message, "approved");
      optionalStringOrNull(message, "reason");
      break;
    case "cancel_turn":
      requireString(message, "turn_id");
      break;
    case "shutdown":
      break;
    case "get_effective_config":
    case "list_mcp_servers":
      requireString(message, "workspace_root");
      break;
    case "save_mcp_server":
      requireString(message, "workspace_root");
      requireString(message, "server_name");
      validateMcpServer(asRecord(message.server, "server must be an object"));
      break;
    case "set_mcp_server_enabled":
      requireString(message, "workspace_root");
      requireString(message, "server_name");
      requireBoolean(message, "enabled");
      break;
    case "delete_mcp_server":
      requireString(message, "workspace_root");
      requireString(message, "server_name");
      break;
    case "session_started":
      requireString(message, "session_id");
      requireString(message, "cwd");
      requireString(message, "provider");
      requireString(message, "model");
      requireOneOf(message, "approval_mode", ["review", "auto", "yolo"]);
      break;
    case "turn_started":
      requireString(message, "session_id");
      requireString(message, "turn_id");
      requireString(message, "cwd");
      break;
    case "text_delta":
    case "reasoning_delta":
      requireString(message, "turn_id");
      requireString(message, "content");
      break;
    case "tool_call":
      requireString(message, "turn_id");
      requireString(message, "tool_id");
      requireString(message, "tool_name");
      optionalString(message, "arguments_summary");
      break;
    case "approval_request":
      requireString(message, "turn_id");
      requireString(message, "approval_id");
      requireString(message, "tool_name");
      optionalString(message, "arguments_summary");
      optionalRecordOrNull(message, "raw_arguments");
      break;
    case "tool_result":
      requireString(message, "turn_id");
      requireString(message, "tool_id");
      optionalBoolean(message, "is_error");
      optionalString(message, "result_summary");
      break;
    case "error":
      requireString(message, "code");
      requireString(message, "message");
      break;
    case "turn_complete":
      requireString(message, "turn_id");
      optionalString(message, "final_text");
      optionalNonNegativeNumber(message, "tool_count");
      optionalNonNegativeNumber(message, "approval_count");
      optionalNonNegativeNumber(message, "iteration_count");
      break;
    case "config_snapshot":
      requireString(message, "workspace_root");
      requireString(message, "provider");
      requireString(message, "model");
      requireOneOf(message, "api_family", ["chat_completions", "responses"]);
      optionalStringOrNull(message, "base_url");
      optionalBoolean(message, "replay_reasoning_content");
      optionalStringArray(message, "config_sources");
      break;
    case "mcp_servers":
      requireString(message, "workspace_root");
      optionalMcpServerSnapshots(message, "servers");
      break;
    case "mcp_server_saved":
      requireString(message, "workspace_root");
      requireString(message, "server_name");
      validateMcpServer(asRecord(message.server, "server must be an object"));
      break;
    case "mcp_server_deleted":
      requireString(message, "workspace_root");
      requireString(message, "server_name");
      break;
  }
}

function validateMcpServer(server: Record<string, unknown>): void {
  optionalBoolean(server, "enabled");
  optionalOneOf(server, "transport", ["stdio", "sse"]);
  optionalStringOrNull(server, "command");
  optionalStringArray(server, "args");
  optionalStringMap(server, "env");
  optionalStringOrNull(server, "cwd");
  optionalPositiveNumber(server, "startup_timeout_seconds");
  optionalStringOrNull(server, "url");
  optionalStringMap(server, "headers");
  optionalStringMap(server, "headers_env");
  optionalPositiveNumber(server, "timeout_seconds");
  optionalPositiveNumber(server, "sse_read_timeout_seconds");
}

function optionalMcpServerSnapshots(message: Record<string, unknown>, key: string): void {
  if (!Object.hasOwn(message, key)) {
    return;
  }
  const value = message[key];
  if (!Array.isArray(value)) {
    throw new ProtocolParseError(`${key} must be an array`);
  }
  for (const item of value) {
    const snapshot = asRecord(item, `${key} entries must be objects`);
    requireString(snapshot, "name");
    optionalStringOrNull(snapshot, "source");
    validateMcpServer(asRecord(snapshot.server, "server must be an object"));
  }
}

function asRecord(value: unknown, message: string): Record<string, unknown> {
  if (!isRecord(value)) {
    throw new ProtocolParseError(message);
  }
  return value;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function requireString(message: Record<string, unknown>, key: string): void {
  const value = message[key];
  if (typeof value !== "string" || value.length === 0) {
    throw new ProtocolParseError(`${key} must be a non-empty string`);
  }
}

function requireBoolean(message: Record<string, unknown>, key: string): void {
  if (typeof message[key] !== "boolean") {
    throw new ProtocolParseError(`${key} must be a boolean`);
  }
}

function requireOneOf(message: Record<string, unknown>, key: string, choices: readonly string[]): void {
  const value = message[key];
  if (typeof value !== "string" || !choices.includes(value)) {
    throw new ProtocolParseError(`${key} must be one of ${choices.join(", ")}`);
  }
}

function optionalString(message: Record<string, unknown>, key: string): void {
  if (Object.hasOwn(message, key) && typeof message[key] !== "string") {
    throw new ProtocolParseError(`${key} must be a string`);
  }
}

function optionalStringOrNull(message: Record<string, unknown>, key: string): void {
  if (Object.hasOwn(message, key) && message[key] !== null && typeof message[key] !== "string") {
    throw new ProtocolParseError(`${key} must be a string or null`);
  }
}

function optionalBoolean(message: Record<string, unknown>, key: string): void {
  if (Object.hasOwn(message, key) && typeof message[key] !== "boolean") {
    throw new ProtocolParseError(`${key} must be a boolean`);
  }
}

function optionalRecord(message: Record<string, unknown>, key: string): void {
  if (Object.hasOwn(message, key)) {
    asRecord(message[key], `${key} must be an object`);
  }
}

function optionalRecordOrNull(message: Record<string, unknown>, key: string): void {
  if (Object.hasOwn(message, key) && message[key] !== null) {
    asRecord(message[key], `${key} must be an object or null`);
  }
}

function optionalStringArray(message: Record<string, unknown>, key: string): void {
  if (!Object.hasOwn(message, key)) {
    return;
  }
  const value = message[key];
  if (!Array.isArray(value) || value.some((item) => typeof item !== "string")) {
    throw new ProtocolParseError(`${key} must be an array of strings`);
  }
}

function optionalStringMap(message: Record<string, unknown>, key: string): void {
  if (!Object.hasOwn(message, key)) {
    return;
  }
  const value = asRecord(message[key], `${key} must be an object`);
  for (const [mapKey, mapValue] of Object.entries(value)) {
    if (typeof mapKey !== "string" || typeof mapValue !== "string") {
      throw new ProtocolParseError(`${key} must be an object of strings`);
    }
  }
}

function optionalOneOf(message: Record<string, unknown>, key: string, choices: readonly string[]): void {
  if (!Object.hasOwn(message, key)) {
    return;
  }
  requireOneOf(message, key, choices);
}

function optionalPositiveNumber(message: Record<string, unknown>, key: string): void {
  if (Object.hasOwn(message, key) && !isPositiveNumber(message[key])) {
    throw new ProtocolParseError(`${key} must be a positive number`);
  }
}

function optionalNonNegativeNumber(message: Record<string, unknown>, key: string): void {
  if (Object.hasOwn(message, key) && !isNonNegativeNumber(message[key])) {
    throw new ProtocolParseError(`${key} must be a non-negative number`);
  }
}

function isPositiveNumber(value: unknown): boolean {
  return typeof value === "number" && Number.isFinite(value) && value > 0;
}

function isNonNegativeNumber(value: unknown): boolean {
  return typeof value === "number" && Number.isFinite(value) && value >= 0;
}

function stripTrailingCarriageReturn(value: string): string {
  return value.endsWith("\r") ? value.slice(0, -1) : value;
}
