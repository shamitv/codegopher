# Config Precedence And Import-Order Fix Approach

Date: 2026-05-19

Branch context: `impl/v0.6-vscode-extension`

## Summary

This note documents the agreed approach for two review findings discovered after the VS Code smoke handoff:

- Config precedence bug: provider endpoint overrides can attach to `providers.openai` even when the final selected provider comes from `CODEGOPHER_PROVIDER`.
- Import-order bug: running `tests/unit/test_config_inspection.py` directly can fail because `codegopher.config.inspection` imports `codegopher.events.protocol`, package initialization imports `codegopher.events.session`, and `events.session` imports `config.inspection`.

These fixes should land before T086/T087 manual smoke gates are finalized.

## Config Precedence Approach

The desired rule is: provider-specific fields must apply to the final selected provider after home, project, environment, and CLI provider/model precedence is resolved.

Current risk:

- `_env_overrides()` and `_cli_overrides()` each create standalone provider entries.
- `_cli_overrides()` applies `base_url` and `api_family` before the final merged provider is known.
- If `CODEGOPHER_PROVIDER=local` and CLI overrides set `--base-url` or `--api-family`, the CLI endpoint fields can land under `providers.openai` while `settings.model.provider` is `local`.

Implementation direction:

- Keep `_env_overrides()` and `_cli_overrides()` focused on scalar/global values and model/provider selection.
- After the base config merge is complete, apply provider-specific environment fields to the final selected provider:
  - `CODEGOPHER_BASE_URL`
  - `CODEGOPHER_API_FAMILY`
  - `CODEGOPHER_API_KEY_ENV`
- Then apply provider-specific CLI fields to the final selected provider:
  - `--base-url`
  - `--api-family`
- Re-apply `CODEGOPHER_API_KEY_ENV` last because there is no CLI flag equivalent and VS Code Secret Storage depends on preserving it.
- Keep the final `CODEGOPHER_API_KEY_ENV` behavior compatible with the VS Code extension:

```text
CODEGOPHER_API_KEY_ENV=HF_TOKEN
HF_TOKEN=<stored VS Code secret>
```

Do not document or commit any real provider token value.

## Import-Order Approach

The direct import failure comes from eager session re-exports in `codegopher.events.__init__`.

Implementation direction:

- Keep protocol models and helpers eagerly re-exported from `codegopher.events`.
- Make session exports lazy in `codegopher.events.__init__` using module-level `__getattr__`.
- Preserve compatibility for imports such as:

```python
from codegopher.events import EventsSession
```

- Avoid importing `codegopher.events.session` during package initialization when a caller only needs `codegopher.events.protocol`.

The direct targeted test must pass without depending on previous test import order:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/unit/test_config_inspection.py
```

## Required Tests

Add or update config loader coverage for these cases:

- `CODEGOPHER_PROVIDER=local` plus CLI `model`, `base_url`, and `api_family` applies endpoint fields to `providers.local`, not `providers.openai`.
- `CODEGOPHER_API_KEY_ENV=LOCAL_API_KEY` remains on the final selected provider when CLI endpoint overrides are present.
- CLI `provider` overriding env `provider` still gets the env-only API key env on the final CLI-selected provider.
- Source labels still include `environment` when only `CODEGOPHER_API_KEY_ENV` is set.

Add or update config inspection/import coverage for these cases:

- `inspect_effective_config()` reports the final selected provider endpoint for env provider plus CLI endpoint overrides.
- Direct import of `codegopher.config.inspection` succeeds.
- Optional compatibility check: `from codegopher.events import EventsSession` still works.

## Verification Commands

Run these after implementing the fixes:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/unit/test_config_loader.py
.\.venv\Scripts\python.exe -m pytest tests/unit/test_config_inspection.py
.\.venv\Scripts\python.exe -m pytest tests/unit/test_imports.py
.\.venv\Scripts\python.exe -m pytest
```

For the VS Code smoke path, rerun the status check after rebuilding/reloading the Extension Development Host:

```text
@codegopher /status
```

Expected status line:

```text
API key env: HF_TOKEN
```

Then rerun:

```text
@codegopher /restart
```

The restart path must not report `OPENAI_API_KEY` when `codegopher.apiKeyEnv` is `HF_TOKEN` and the token has been stored with `CodeGopher: Set API Key`.
