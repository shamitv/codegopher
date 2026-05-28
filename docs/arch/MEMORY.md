# Memory Architecture

CodeGopher has two memory-like context sources with different lifetimes:

- Persistent memory is local JSON state under the CodeGopher data home.
- Episode memory is task-local runtime state owned by an active `AgentSession`.

Persistent memory is for user-approved facts that should survive future turns or projects. Episode memory is for current-task observations such as inspected files, searches, TODO updates, report writes, tool errors, unresolved pivots, and final decisions.

## Persistent Storage

- `MemoryStore` roots data at `<data_home>/memory`.
- Session memory is keyed by a hash of the TUI session id.
- Project memory is keyed by a hash of the canonical cwd.
- Memory entries use stable ids, timestamps, scope, source, content, and optional tags.
- CRUD writes use a temporary file and replace the target JSON file.

## Episode State

- `EpisodeState` is in-memory only and is not backed by disk.
- `AgentSession` creates episode state when the tool context does not already provide one.
- Episode entries use stable ids, kind, summary, references, and timestamps.
- The runtime records compact observations for read/search/list tools, TODO updates, chained report writes, tool errors, and assistant final responses.
- Episode state is injected into provider context under `Runtime episode memory`.
- Compaction prompts include episode memory so summaries preserve inspected evidence and unresolved pivots.
- TUI resume does not restore episode state; tools must inspect again after a resumed process starts.

## Safety

- Persistent memory content is redacted before persistence.
- Inline `api_key`, `token`, `secret`, and `password` assignments are replaced with `[REDACTED]`.
- Raw environment values are redacted when the environment variable name looks secret-bearing.
- Memory files must not contain API keys, raw environment values, provider hidden payloads, or access-tracker grants.
- Episode memory also redacts endpoint URLs, local temp paths, and secret-like assignments before context injection.
- Benchmark progress, audit evidence, proxy data, and temp workspace paths must not be saved to persistent memory unless the user explicitly requests a sanitized memory.

## `save_memory`

- `save_memory` is a model-facing tool and requires approval.
- Tool input is `scope = "session" | "project"` plus `content`.
- Headless runs can save project memory.
- Session memory requires a stable session id, normally from the TUI session.
- Disabled memory settings produce clear tool errors instead of writing files.

## Context Injection

- `AgentSession` loads selected session and project memories before provider calls.
- Selected memories are rendered in the system prompt under `Selected memories`.
- Episode memory is rendered separately under `Runtime episode memory` and described as task-local, not persistent.
- Newly saved project memory can appear in the next provider call in the same agent turn.
- `/memory` lists session and project memories in the TUI.
- `/forget ID --yes` deletes a memory after an explicit confirmation step.
- Memory save and delete events are rendered as visible TUI messages for transparency.
