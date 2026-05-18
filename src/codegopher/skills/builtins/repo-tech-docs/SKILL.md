---
name: Repository Technical Documentation
description: Extract technical documentation from an existing repository, including architecture, module map, setup, APIs, configuration, data flows, tests, operations, dependencies, and maintenance notes. Use when asked to document how a codebase is built, run, integrated, deployed, or maintained.
keywords: technical docs, architecture docs, setup docs, api docs, module map, operations, dependencies
---
# Repository Technical Documentation

Use this skill to document how the repository works from an engineering perspective.

## Workflow

- Start from README files, package manifests, config loaders, entry points, tests, scripts, Docker or CI files, API routes, schemas, migrations, and deployment notes.
- Prefer repository facts over generic framework descriptions.
- Explain the system at multiple levels: runtime entry points, package/module structure, request or job flow, storage, external services, and verification.
- Record assumptions, missing setup details, and risks as explicit gaps.
- Keep docs useful for a new maintainer who needs to build, run, test, debug, and safely change the project.

## Coverage

- Architecture overview and major runtime components.
- Module map with responsibilities and ownership boundaries.
- Local setup, configuration, environment variables, and secrets handling.
- API surfaces, commands, scheduled jobs, events, queues, and integration points.
- Data model, persistence, migrations, caches, and data flow.
- Test strategy, fixtures, useful commands, and known slow or external checks.
- Build, packaging, deployment, observability, and operational notes.
- Dependencies, version constraints, generated files, and upgrade concerns.

## Output

- If the user asks for a written artifact, default to `docs/technical/` and create focused Markdown files such as `ARCHITECTURE.md`, `SETUP.md`, `API.md`, or `OPERATIONS.md`.
- If the user does not ask for files, produce a structured report in chat.
- Include source references for non-obvious implementation details.
