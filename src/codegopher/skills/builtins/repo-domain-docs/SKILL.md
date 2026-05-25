---
name: Repository Domain Documentation
description: Extract business and functional domain documentation from an existing repository, including actors, workflows, use cases, data entities, bounded contexts, glossary, business rules, and open questions. Use when asked to document product behavior, business domain, functional requirements, or domain models from source code.
keywords: domain docs, business docs, functional docs, glossary, workflows, use cases, bounded contexts
---
# Repository Domain Documentation

Use this skill to document what the repository does from a business and functional perspective.

## Workflow

- CodeGopher may activate a mission contract for this skill. Use the session TODO ledger as the source of truth for coverage: add or update TODOs for capability inventory, actors/workflows, entities/lifecycle states, business rules, glossary, source evidence, and open questions.
- Treat the mission ledger as active task state, not long-term memory. Do not save repository-specific task progress to persistent memory unless the user explicitly asks.
- Start from product docs, README files, route maps, schemas, migrations, tests, fixtures, seed data, user-facing strings, and service boundaries.
- Extract domain facts from code and tests; do not invent business behavior that is not evidenced by the repository.
- Separate confirmed behavior from inferred behavior and open questions.
- Prefer user language from the product and tests over implementation jargon when naming workflows and domain concepts.
- Cross-reference technical identifiers only when they help a reader trace the domain fact back to code.

## Coverage

- Business purpose and product capabilities.
- Actors, roles, permissions, and external systems.
- Core entities, relationships, lifecycle states, and important attributes.
- Workflows, use cases, commands, decisions, and exceptional paths.
- Business rules, validation rules, invariants, and policy constraints.
- Bounded contexts, module ownership, and integration points.
- Glossary of terms with source evidence.
- Unknowns, contradictions, and areas needing product confirmation.

## Output

- If the user asks for a written artifact, default to `docs/domain/` and create focused Markdown files such as `OVERVIEW.md`, `WORKFLOWS.md`, `GLOSSARY.md`, or `OPEN_QUESTIONS.md`.
- If the user does not ask for files, produce a structured report in chat.
- Include a short evidence note for important claims, using file paths or test names where useful.
- Before finishing, self-check the active TODO ledger and explicitly note confirmed behavior, inferred behavior, unknowns, and unreviewed areas.
