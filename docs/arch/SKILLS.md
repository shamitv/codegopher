# Skills Architecture

CodeGopher skills are read-only Markdown instruction files discovered from project, user, and built-in locations.

## Discovery And Loading

- Project skills live under `.codegopher/skills/*/SKILL.md`.
- User skills live under `~/.codegopher/skills/*/SKILL.md`.
- Built-in skills ship under the Python package at `codegopher.skills.builtins`.
- Skills load into provider context through `/skills load ID`, explicit `@skill:ID`, or keyword autoload.
- Skill loading reads only `SKILL.md`; sibling files do not execute and do not register tools.

## Built-In Skill Packs

CodeGopher ships built-in Markdown skills for repository documentation and static security review:

- `repo-domain-docs`: extract business and functional domain documentation from an existing repository.
- `repo-tech-docs`: extract technical architecture, setup, API, test, dependency, and operations documentation.
- `crud-owasp-static-audit`: review CRUD web application source against OWASP Top 10:2025.
- `chained-vulnerability-static-audit`: perform static attack-chain review and write `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`.

`cgopher init --skill-pack repo-docs|security|chained-vulns|all` copies packaged skill files into project `.codegopher/skills`. Existing files are skipped unless `--force` is used.

## Security Boundary

The CRUD OWASP and chained-vulnerability skills are static-only. They may inspect source, routes, controllers, auth code, models, migrations, config, dependencies, logging, errors, and tests. They must not run live HTTP probing, fuzzing, credential attacks, dynamic scanners, exploit payloads, or network tests.

When the chained-vulnerability skill is active, CodeGopher uses a restricted static-audit tool registry:

- Allowed read/search tools are wrapped by static-audit policy checks.
- Shell, MCP, arbitrary writes, edits, and persistent memory writes are unavailable.
- Hidden evaluator metadata, dotfile paths, parent traversal, and answer-key terminology searches are denied at the tool layer.
- The only write path is `write_chained_vulnerability_report`, which writes the dedicated chained-audit report.

## Mission Contracts

Selected complex skills activate mission contracts. The chained-vulnerability contract seeds TODOs for discovery, working candidate ledger updates, chain synthesis, negative evidence, report writing, and self-check. Completion requires the report writer call and the report artifact.

The chained-audit report is also validated before the mission can complete. The report must include a `Candidate Chain Ledger`, fenced JSON with a top-level `candidate_chains` array, repository-relative path evidence, symbols, line or line-range evidence, safe-control classifications, and negative evidence for incomplete or rejected no-chain conclusions.
