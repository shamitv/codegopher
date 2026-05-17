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
- Smoke test real OpenAI-compatible endpoint, when available: `OPENAI_API_KEY=dummy-key cgopher -p "Reply with exactly: codegopher-smoke-ok" --json`.
- Smoke test project initialization: `cgopher init` creates `.codegopher/skills/project/SKILL.md` without writing settings or secrets.
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
- Tag the release only after the branch is pushed and CI is green.
