from __future__ import annotations

from click.testing import CliRunner

from codegopher.cli.main import app


def test_cli_without_prompt_shows_alpha_message() -> None:
    result = CliRunner().invoke(app)

    assert result.exit_code == 0
    assert "CodeGopher v0.1 alpha" in result.output


def test_cli_prompt_dry_run_echoes_prompt() -> None:
    result = CliRunner().invoke(app, ["-p", "hello"], env={"CODEGOPHER_TEST_MOCK_RESPONSE": "mocked"})

    assert result.exit_code == 0
    assert result.output == "mocked\n"


def test_cli_applies_settings_overrides() -> None:
    result = CliRunner().invoke(
        app,
        ["-p", "hello", "--model", "local-model", "--provider", "local"],
        env={"CODEGOPHER_TEST_MOCK_RESPONSE": "mocked"},
    )

    assert result.exit_code == 0
    assert result.output == "mocked\n"
