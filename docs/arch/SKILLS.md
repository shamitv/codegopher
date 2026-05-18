# Skills Architecture

CodeGopher skills are read-only Markdown instruction files discovered from project, user, and built-in locations.

## Discovery And Loading

- Project skills live under `.codegopher/skills/*/SKILL.md`.
- User skills live under `~/.codegopher/skills/*/SKILL.md`.
- Built-in skills ship under the Python package at `codegopher.skills.builtins`.
- Skills load into provider context through `/skills load ID`, explicit `@skill:ID`, or keyword autoload.
- Skill loading reads only `SKILL.md`; sibling files do not execute and do not register tools.

## Built-In Skill Packs

v0.5 adds three built-in Markdown skills:

- `repo-domain-docs`: extract business and functional domain documentation from an existing repository.
- `repo-tech-docs`: extract technical architecture, setup, API, test, dependency, and operations documentation.
- `crud-owasp-static-audit`: review CRUD web application source against OWASP Top 10:2025.

`cgopher init --skill-pack repo-docs|security|all` copies packaged skill files into project `.codegopher/skills`. Existing files are skipped unless `--force` is used.

## Security Boundary

The CRUD OWASP skill is static-only. It may inspect source, routes, controllers, auth code, models, migrations, config, dependencies, logging, errors, and tests. It must not run live HTTP probing, fuzzing, credential attacks, dynamic scanners, exploit payloads, or network tests.
