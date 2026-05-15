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
- Tag the release only after the branch is pushed and CI is green.

