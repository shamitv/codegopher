# Release Checklist

Use this checklist before publishing a CodeGopher release.

- Confirm `CHANGELOG.md` has the release notes.
- Run `ruff check src/ tests/`.
- Run `mypy src/`.
- Run `python -m pytest`.
- Run `python -m hatch build`.
- Install the built wheel in a clean virtual environment.
- Smoke test `codegopher --help`.
- Smoke test `cgopher -p "hello" --json` with a configured provider or the local test mock.
- Smoke test implicit project init in a disposable project: first `cgopher -p "hello"` creates `.codegopher/skills/project/SKILL.md`, while `cgopher --no-project-init -p "hello"` does not create `.codegopher/`.
- Smoke test real OpenAI-compatible endpoint, when available: `OPENAI_API_KEY=dummy-key cgopher -p "Reply with exactly: codegopher-smoke-ok" --json`.
- Smoke test Responses API, when available: `cgopher --api-family responses -p "Reply with exactly: codegopher-responses-ok" --json`.
- Smoke test MCP stdio with a disposable server config; confirm discovered tools are named `mcp__SERVER__TOOL`, require approval, and sessions close after exit.
- Smoke test MCP SSE with a controlled endpoint; use `headers_env` for sensitive headers and confirm resolved values are not printed or persisted.
- Smoke test Playwright MCP, when Node.js and browser dependencies are available: `npx @playwright/mcp@latest --headless --isolated`.
- Smoke test project initialization: `cgopher init` creates `.codegopher/skills/project/SKILL.md` without writing settings or secrets.
- Smoke test v0.5 skill-pack initialization: `cgopher init --skill-pack repo-docs`, `cgopher init --skill-pack security`, and `cgopher init --skill-pack all` create the expected `.codegopher/skills/*/SKILL.md` files without writing settings or secrets.
- Smoke test interactive TUI startup with `cgopher` in a real terminal.
- Smoke test TUI slash commands: `/help`, `/model`, `/mode`, `/stats`, `/clear`, `/compact`, `/memory`, `/forget`, `/skills`, and `/todo`.
- Smoke test TUI file mentions and `/shell COMMAND` approval/denial flows in a disposable project.
- Smoke test TUI session auto-resume for the same cwd.
- Smoke test v0.3 context, memory, skills, and TODO flows:
  - `/stats` shows context budget status.
  - `/compact [instructions]` records a visible compaction summary.
  - `save_memory` creates an approved memory and `/memory` lists it.
  - `/skills` lists project/user/built-in skills and `/skills load ID` loads one.
  - `/todo add TEXT` and `/todo done ID` update visible session TODO state.
- Smoke test v0.5 built-in skills:
  - `@skill:repo-domain-docs` reaches provider context and can produce a domain documentation outline.
  - `@skill:repo-tech-docs` reaches provider context and can produce a technical documentation outline.
  - `@skill:crud-owasp-static-audit` reaches provider context and keeps the OWASP Top 10:2025 review static-only.
- Tag the release only after the branch is pushed and CI is green.
