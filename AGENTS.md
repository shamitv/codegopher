# AGENTS.md - CodeGopher Contribution Guidance

This file gives coding agents and human contributors the project-specific rules for
working in the CodeGopher repository.

## Project Purpose

CodeGopher is a Python-native, provider-agnostic AI coding agent. It includes:

- A headless Click CLI exposed as `codegopher`, `cgopher`, and `python -m codegopher`.
- A Textual TUI for iterative local sessions.
- A VS Code chat bridge that communicates through JSONL events.
- Markdown skills, mission contracts, session TODOs, memory, context compaction, and MCP tools.
- Static security reporting, including chained vulnerability audit report writing.

Treat the repository as an agent runtime first. Preserve predictable CLI behavior,
tool safety, provider compatibility, and source-grounded reporting.

## Repository Rules

- Prefer existing patterns under `src/codegopher` before introducing new abstractions.
- Keep edits scoped to the requested behavior and nearby ownership boundaries.
- Do not add a public benchmark command. Benchmark tooling must remain internal under
  `codegopher.devtools.benchmark`.
- Keep security skills static-only. Do not add live probing, fuzzing, credential
  attacks, exploit scripts, dynamic scanners, port scans, or external network tests.
- Do not store secrets in docs, reports, memories, traces, event logs, tests, or
  committed artifacts. Redact endpoint URLs, API keys, proxy admin URLs, usernames,
  local temp roots, and original corpus paths from committed summaries.
- Keep generated benchmark event logs, stderr logs, temp workspaces, proxy snapshots,
  generated reports, and raw per-app summaries out of committed docs unless the user
  explicitly asks for a summarized artifact with placeholders.
- Respect `.codegopherignore` and project boundaries when adding file access behavior.
- Do not revert unrelated user changes. If unrelated files are dirty, leave them alone.

## Development Workflow

Install the package with development dependencies:

```bash
pip install -e ".[dev]"
```

Use focused verification for local changes:

```bash
python -m pytest <tests>
```

Use full Python verification before broad or release-facing changes:

```bash
python -m pytest
python -m ruff check src tests
python -m mypy src
```

When touching `extensions/vscode`, also verify the extension:

```bash
cd extensions/vscode
npm install
npm run compile
npm run lint
npm test
```

For documentation-only changes, full tests are usually unnecessary. Still check the
changed files for consistency with README, architecture docs, and existing examples.

## Built-In Skills

CodeGopher ships built-in Markdown skills under `src/codegopher/skills/builtins`.
When changing skill behavior:

- Keep documentation skills source-grounded. They should cite repository facts and
  explicitly mark assumptions, gaps, and open questions.
- Keep security skills static-only and report-oriented.
- Preserve mission contract expectations for complex skills: task ledger updates,
  final artifact creation when required, and completion self-checks.
- For chained audits, final evidence should use full repository-relative paths,
  exact symbols, and line or line-range references.

## Validating Documentation And Vulnerability Scan Skills With secure-code-hunt

Use `D:\work\secure-code-hunt` as an external validation corpus for documentation
and security skill behavior. Do not copy evaluator files, raw benchmark artifacts,
or hidden manifests into CodeGopher.

Before any validation run, create a sanitized scan workspace. Follow:

```text
D:\work\secure-code-hunt\docs\howto\sanitization.md
```

The agent-visible scan workspace must not contain:

- `.vulns`
- `scenarios.md`
- app `README.md`
- `docs/tech/architecture.md`
- `tests/`, `src/test/`, or `__tests__/`
- `.venv/`, `node_modules/`, `dist/`, `build/`, or `target/`

Also verify that agent-visible source and docs do not contain answer-key terms such
as `VULNERABILITY`, `CHAIN LINK`, `DECOY`, `OWASP`, or `CWE`.

### Documentation Skill Validation

Validate `@skill:repo-tech-docs` and `@skill:repo-domain-docs` against sanitized
source-only app copies. Prefer representative apps such as:

- `D:\work\secure-code-hunt\apps\python\app-03-banking-service`
- `D:\work\secure-code-hunt\apps\python\app-46-charity-donations`

Success criteria:

- Technical and domain summaries cite source files, routes, schemas, tests, or
  configuration that are present in the sanitized workspace.
- Output does not cite `.vulns`, `scenarios.md`, app README files, removed docs, or
  original corpus paths.
- Open questions and inferred behavior are explicitly separated from confirmed facts.
- The skill does not invent product behavior or business rules without source evidence.

### Chained Vulnerability Skill Validation

Validate `@skill:chained-vulnerability-static-audit` through the internal benchmark
harness or a sanitized manual workspace. The audit must remain source-only.

Required outcome:

- `write_chained_vulnerability_report` is called when the report writer is available.
- The generated report exists at `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`.
- The report includes a `Candidate Chain Ledger`.
- The report includes a fenced JSON candidate ledger with `candidate_chains`.
- Evidence rows include full relative path, exact symbol, and line or line range.
- Tool use stays within the sanitized workspace, with no parent traversal, shell
  execution, live probing, MCP calls, memory writes, or arbitrary writes.

Ground-truth comparison against hidden `.vulns` files must happen outside the
agent-visible workspace. Use those manifests only for evaluator scoring, never as
context for the scanning agent.

## Benchmark Reporting

Committed benchmark summaries should be durable and leak-safe. Include aggregate
metrics, app display names, and placeholder endpoint/proxy values only. Do not commit
raw local endpoints, proxy admin URLs, API keys, temp directories, usernames, raw
event logs, or generated per-app workspaces.

The current chained-audit evaluation is useful for analyst-assisted review and
evidence collection. Do not present it as unattended security signoff.
