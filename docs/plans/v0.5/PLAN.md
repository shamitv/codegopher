# CodeGopher v0.5 Implementation Plan

This plan covers the v0.5 implementation slice: built-in repository documentation and static security skill packs on top of the v0.3 Markdown skill system.

The v0.4 Providers And MCP roadmap slot remains reserved in `docs/plans/v0.4`. Advanced coding workflows move to a later roadmap slot.

## Summary

The v0.5 release should make CodeGopher useful for repeatable repository understanding tasks without adding executable skill runtimes.

Target user experience:

```bash
cgopher init --skill-pack repo-docs
cgopher init --skill-pack security
cgopher -p "use @skill:repo-domain-docs to summarize this repo"
cgopher -p "use @skill:crud-owasp-static-audit to review this CRUD app"
```

The release ships built-in Markdown skills for:

- business and functional domain documentation,
- technical repository documentation,
- static-only CRUD application security review against OWASP Top 10:2025.

## User-Facing Interfaces

Existing interfaces stay compatible:

- `cgopher init [PATH]`: keep creating the default `project` skill.
- `cgopher init [PATH] --force`: keep overwriting the default `project` skill.
- `/skills`, `/skills load ID`, and `@skill:ID`: keep loading discovered skills.

New init interface:

- `cgopher init [PATH] --skill-pack repo-docs`: materialize `repo-domain-docs` and `repo-tech-docs`.
- `cgopher init [PATH] --skill-pack security`: materialize `crud-owasp-static-audit`.
- `cgopher init [PATH] --skill-pack all`: materialize all v0.5 built-in skills.
- `--force`: overwrite existing materialized skill files; without it, skip existing files and continue with the rest of the pack.

## Implementation Shape

Add built-in Markdown skills under `src/codegopher/skills/builtins/`:

- `repo-domain-docs`: extracts business purpose, actors, workflows, use cases, entities, business rules, glossary, bounded contexts, and open questions. File output defaults to `docs/domain/` only when requested.
- `repo-tech-docs`: extracts architecture, module map, setup, APIs, configuration, data flow, tests, operations, dependencies, and maintenance notes. File output defaults to `docs/technical/` only when requested.
- `crud-owasp-static-audit`: performs source-only CRUD app review against OWASP Top 10:2025. File output defaults to `docs/security/OWASP_TOP10_2025_REVIEW.md` only when requested.

Extend `cgopher init` with a skill-pack option that copies the packaged `SKILL.md` files into project `.codegopher/skills/<id>/SKILL.md`.

## Safety And Scope

- Skills remain read-only Markdown context.
- No executable skill runtime, scripts, scanners, or new dependencies are added.
- The security skill is static-only: it must not run live HTTP probing, fuzzing, credential attacks, dynamic scanners, exploit payloads, or network tests.
- The security skill must separate confirmed findings from unknown or not-reviewed areas.

Out of scope for v0.5:

- Provider or MCP implementation.
- Active penetration testing.
- External Codex `$CODEX_HOME/skills` installation.
- Sub-agents, git worktree helpers, or sandboxing.

## Testing Plan

Expected test layers:

- Built-in skill discovery tests for all new skill ids, metadata, and context content.
- CLI tests for `cgopher init --skill-pack repo-docs`, `security`, `all`, skip behavior, `--force`, and no secret/settings writes.
- Integration tests proving `@skill:repo-domain-docs`, `@skill:repo-tech-docs`, and `@skill:crud-owasp-static-audit` reach provider context.
- Static safety assertions proving the OWASP skill documents the static-only boundary and does not recommend active tools.
- Documentation checks for roadmap, release checklist, and architecture notes.

Final v0.5 verification:

```bash
source .venv/bin/activate
ruff check src/ tests/
mypy src/
python -m pytest
python -m hatch build
```
