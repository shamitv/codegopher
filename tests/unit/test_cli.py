from __future__ import annotations

from click.testing import CliRunner

from codegopher.cli.main import app


def test_cli_without_prompt_shows_alpha_message() -> None:
    result = CliRunner().invoke(app)

    assert result.exit_code == 0
    assert "CodeGopher v0.1 alpha" in result.output


def test_cli_prompt_dry_run_echoes_prompt() -> None:
    result = CliRunner().invoke(app, ["-p", "hello"])

    assert result.exit_code == 0
    assert "CodeGopher dry run: hello" in result.output

