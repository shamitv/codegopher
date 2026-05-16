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
- Smoke test interactive TUI startup with `cgopher` in a real terminal.
- Smoke test TUI slash commands: `/help`, `/model`, `/mode`, `/stats`, and `/clear`.
- Smoke test TUI file mentions and `/shell COMMAND` approval/denial flows in a disposable project.
- Smoke test TUI session auto-resume for the same cwd.
- Tag the release only after the branch is pushed and CI is green.
