# LLM Proxy Testing And Analysis

This guide describes how to use a local LLM proxy for development-only testing,
benchmark analysis, and troubleshooting in CodeGopher.

Use this workflow when you need visibility into request volume, token/cost
patterns, model-routing behavior, or failure modes that are hard to diagnose
from app-level summaries alone.

## Scope And Safety

- Proxy-based benchmark work is internal only under
  `codegopher.devtools.benchmark`.
- Do not add or expose a public `cgopher benchmark` command.
- Keep static security audits source-only; do not use proxy workflows to justify
  live probing or exploit behavior.
- Do not commit raw proxy logs, proxy snapshots, raw endpoint values,
  API key names/values, local usernames, temp roots, or original corpus paths.
- Commit only sanitized aggregate conclusions and placeholders.

## When To Use A Proxy

Use proxy capture when required for:

- Analysis:
  compare model runs by requests, token volume, retry patterns, and wall time.
- Troubleshooting:
  confirm model routing, detect mixed-model buckets, and investigate provider
  failures or malformed tool-call recovery behavior.
- Validation hygiene:
  ensure run artifacts remain leak-safe before publishing committed summaries.

## Benchmark CLI Integration

The benchmark CLI can start and end a proxy stats run around the benchmark
execution when a proxy admin API is provided.

Relevant options:

- `--proxy-admin-url`: proxy admin base URL used to start/end stats runs.
- `--proxy-run-name`: optional human-readable run label.
- `--proxy-run-notes`: optional notes persisted with the proxy run.
- `--proxy-run-url`: optional run URL override for report metadata.

Timeout and retries still come from benchmark flags such as
`--timeout-seconds` and `--retries`.

## Recommended Run Flow

1. Ensure there is no active proxy run before starting.
2. Start a fresh proxy run for one model and one benchmark command.
3. Execute the benchmark suite.
4. End the proxy run and capture the final run snapshot.
5. Build sanitized summaries from aggregate metrics only.
6. Repeat with a separate fresh run for each model to avoid cross-model
   contamination.

The proxy client fails fast if an active run exists, so contamination is caught
before the benchmark starts.

## Example Command

Use placeholders for local values:

```bash
python -m codegopher.devtools.benchmark \
  --suite docs/plans/v0.14/suite.toml \
  --output-dir tmp/bench-out \
  --cgopher .venv/bin/cgopher \
  --model MODEL_ALIAS \
  --base-url LOCAL_OPENAI_COMPATIBLE_ENDPOINT \
  --api-family responses \
  --api-key-env OPENAI_API_KEY \
  --api-key-value DUMMY_KEY \
  --timeout-seconds 900 \
  --retries 1 \
  --proxy-admin-url PROXY_ADMIN_BASE_URL \
  --proxy-run-name "v0.14 focused MODEL_ALIAS" \
  --proxy-run-notes "focused validation"
```

## Analysis Checklist

For each completed run, review:

- request totals and any unexpected route mix
- token totals and cost trends
- retry counts and error categories
- per-app completion and report-writer completion status
- malformed tool-call outcomes and recovered malformed counts
- candidate-flow and quality-gate outcomes (when applicable)

If the proxy bucket includes requests from another model or unrelated traffic,
separate primary benchmark metrics from full proxy metrics and document the caveat.

## Troubleshooting Patterns

- Unexpected model behavior:
  verify requested model versus proxy-observed upstream model.
- Sudden cost increase without recall gain:
  inspect retries, malformed outputs, and long corrective loops.
- Missing or partial benchmark metrics:
  check whether proxy run start/end succeeded and whether a run overlapped.
- Run-to-run variance:
  use one fresh proxy run per model and keep the app subset fixed.

## Artifact Hygiene

Before committing docs:

- replace endpoint and proxy URLs with placeholders
- remove local absolute paths and usernames
- remove API key names/values and local temp roots
- avoid committing raw event logs, raw proxy snapshots, and generated temp workspaces

Committed benchmark docs should contain only durable, sanitized conclusions.

## Related Files

- `src/codegopher/devtools/benchmark/__main__.py`
- `src/codegopher/devtools/benchmark/proxy.py`
- `docs/eval/README.md`
- `AGENTS.md`
