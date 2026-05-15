from __future__ import annotations

import json

from click.testing import CliRunner

import codegopher.cli.main as cli_main
from codegopher.cli.main import app
from codegopher.core.agent import AgentResult


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


def test_cli_appends_piped_stdin_to_prompt(monkeypatch) -> None:
    captured: dict[str, str] = {}

    async def fake_run_agent(**kwargs):
        captured["prompt"] = kwargs["prompt"]
        return AgentResult(final_text="ok", iterations=1)

    monkeypatch.setattr(cli_main, "run_agent", fake_run_agent)

    result = CliRunner().invoke(
        app,
        ["-p", "summarize"],
        input="log line\n",
        env={"CODEGOPHER_TEST_MOCK_RESPONSE": "unused"},
    )

    assert result.exit_code == 0
    assert captured["prompt"] == "summarize\n\nInput context:\nlog line\n"


def test_cli_json_output_shape() -> None:
    result = CliRunner().invoke(
        app,
        ["-p", "hello", "--json"],
        env={"CODEGOPHER_TEST_MOCK_RESPONSE": "mocked"},
    )

    assert result.exit_code == 0
    assert json.loads(result.output) == {
        "final_text": "mocked",
        "tool_results": [],
        "iterations": 1,
    }


def test_cli_reports_configuration_errors() -> None:
    result = CliRunner().invoke(
        app,
        ["-p", "hello"],
        env={
            "CODEGOPHER_TEST_MOCK_RESPONSE": "mocked",
            "CODEGOPHER_APPROVAL_MODE": "sometimes",
        },
    )

    assert result.exit_code != 0
    assert "Invalid settings" in result.output


def test_cli_reports_provider_errors() -> None:
    result = CliRunner().invoke(
        app,
        ["-p", "hello"],
        env={"OPENAI_API_KEY": "", "CODEGOPHER_TEST_MOCK_RESPONSE": None},
    )

    assert result.exit_code != 0
    assert "Missing API key" in result.output
