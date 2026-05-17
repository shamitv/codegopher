# Memory Architecture

CodeGopher memory is local JSON state under the CodeGopher data home, not project runtime config.

## Storage

- `MemoryStore` roots data at `<data_home>/memory`.
- Session memory is keyed by a hash of the TUI session id.
- Project memory is keyed by a hash of the canonical cwd.
- Memory entries use stable ids, timestamps, scope, source, content, and optional tags.
- CRUD writes use a temporary file and replace the target JSON file.

## Safety

- Memory content is redacted before persistence.
- Inline `api_key`, `token`, `secret`, and `password` assignments are replaced with `[REDACTED]`.
- Raw environment values are redacted when the environment variable name looks secret-bearing.
- Memory files must not contain API keys, raw environment values, provider hidden payloads, or access-tracker grants.

## `save_memory`

- `save_memory` is a model-facing tool and requires approval.
- Tool input is `scope = "session" | "project"` plus `content`.
- Headless runs can save project memory.
- Session memory requires a stable session id, normally from the TUI session.
- Disabled memory settings produce clear tool errors instead of writing files.

## Context Injection

- `AgentSession` loads selected session and project memories before provider calls.
- Selected memories are rendered in the system prompt under `Selected memories`.
- Newly saved project memory can appear in the next provider call in the same agent turn.
- Memory commands such as `/memory` and `/forget` are planned later and are not part of this milestone.
