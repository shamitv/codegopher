# CodeGopher v0.8 Implementation Plan - Development Benchmark Infrastructure

This plan covers the v0.8 implementation slice: improve chained vulnerability audit quality and add internal benchmark automation driven by the v0.7 benchmark findings.

The v0.7 benchmark detected all planted ground-truth chains across Django/Python, Spring Boot/Java, and NestJS/TypeScript apps with full component recall and zero safety violations. v0.8 turns the manual benchmark workflow into development-only tooling and improves report quality so future measurements are easier to compare.

## Findings Summary From v0.7

- All three apps produced reports via `write_chained_vulnerability_report`.
- All planted ground-truth chains were detected with all known components identified.
- The static audit tool policy held: no unsafe tool calls, denied results, or path escapes.
- Reasoning replay fixed the DeepSeek-compatible upstream failure.
- Generated reports included extra candidate chains beyond the `.vulns` manifests, so v0.8 measures ground-truth recall and unmatched candidates instead of claiming exhaustive precision/F1.

## Development-Only Interfaces

No public `cgopher benchmark` command will be added in v0.8.

Benchmark runs are invoked by maintainers with:

```bash
python -m codegopher.devtools.benchmark \
  --suite tests/fixtures/security/benchmark-suite.toml \
  --output-dir docs/plans/v0.8/report/<yyyyMMdd-HHmmss> \
  --cgopher .venv/Scripts/cgopher.exe \
  --model Qwen/Qwen3.6-35B-A3B \
  --base-url LOCAL_OPENAI_COMPATIBLE_ENDPOINT \
  --api-family chat_completions \
  --replay-reasoning-content
```

The existing user-facing audit interfaces remain unchanged:

- `@skill:chained-vulnerability-static-audit`
- TUI `/audit --chain`
- normal prompt usage through headless CLI, TUI, or VS Code chat

## Implementation Shape

### 1. Internal Benchmark Tooling

Add `codegopher.devtools.benchmark` as an internal, compatibility-free development namespace. It provides:

- `.vulns` manifest parsing and suite/app definitions.
- Code-only workspace isolation that strips `README.md`, `impl_plan.md`, `.vulns`, and nested copies.
- Subprocess execution of `cgopher --events` with explicit model, endpoint, API family, API key env, timeout, retry, and reasoning replay settings.
- Event log, stderr, final text, generated report, ground-truth, per-app analysis, JSON summary, and aggregate Markdown artifact capture.
- Safety analysis for removed docs, parent/original path attempts, unsafe tools, denied tool results, and output mentions of hidden evaluator files.

### 2. Evaluation Semantics

Evaluation reports:

- ground-truth chain status: full, partial, or missed;
- component-level recall for source/hop/sink steps;
- report quality signals such as line-reference count and source-reference hits;
- unmatched candidate chain titles for manual review.

It does not report precision or F1 unless a manifest is explicitly exhaustive. Extra detected chains are treated as candidate findings, not automatic false positives.

### 3. Audit Skill Quality

Update `chained-vulnerability-static-audit` so reports are more benchmarkable:

- require file path, line number or range, and symbol evidence for every source, hop, and sink;
- always call the dedicated report writer when available, including no-chain runs;
- include confidence calibration: High is statically proven, Medium depends on runtime behavior, Low is weakly supported;
- include a cross-cutting weaknesses section for security issues that do not form complete chains.

### 4. Product Docs

Update roadmap/status/TODO docs so v0.8 is "Audit Quality And Development Benchmark Infrastructure" and clearly not a public product surface. Richer IDE UI/webview work remains deferred to a later slice.

## Testing Plan

Unit tests:

- manifest and suite parsing;
- workspace isolation;
- event parsing and process capture;
- safety analysis;
- ground-truth recall and report-quality evaluation;
- Markdown/JSON report generation;
- skill wording for source references, no-chain report writing, confidence, and cross-cutting weaknesses.

Integration tests:

- mocked development benchmark runner that creates expected artifacts;
- regression test proving `cgopher benchmark` is not exposed as a public command.

Release gates:

```bash
python -m pytest
python -m ruff check .
python -m mypy src

cd extensions/vscode
npm run compile
npm run lint
npm test
```

Real-LLM verification:

- Run the internal benchmark against the three sample benchmark apps with `OPENAI_API_KEY=dummy-key`, `LOCAL_OPENAI_COMPATIBLE_ENDPOINT`, `chat_completions`, `Qwen/Qwen3.6-35B-A3B`, and reasoning replay enabled.
- Archive results under `docs/plans/v0.8/report/<yyyyMMdd-HHmmss>`.

## Out Of Scope

- Public benchmark CLI or compatibility guarantees.
- Dynamic/runtime vulnerability testing.
- Automated remediation or code-fix generation.
- Exhaustive vulnerability discovery claims.
- Richer IDE UI and webview work.
