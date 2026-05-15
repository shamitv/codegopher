from __future__ import annotations

import json

import pytest
from click.testing import CliRunner

import codegopher.cli.main as cli_main
from codegopher.cli.main import app
from codegopher.config.schema import ModelConfig, ProviderEntry, Settings
from codegopher.core.agent import AgentResult
from codegopher.core.errors import ProviderError
from codegopher.providers.openai_compat import OpenAICompatProvider
from codegopher.runtime import build_provider


def test_cli_without_prompt_requires_interactive_tty() -> None:
    result = CliRunner().invoke(app)

    assert result.exit_code != 0
    assert "pass -p/--prompt for headless usage" in result.output


def test_cli_without_prompt_launches_tui_when_interactive(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_launch_tui(settings: Settings, *, cwd) -> None:
        captured["settings"] = settings
        captured["cwd"] = cwd

    monkeypatch.setattr(cli_main, "_streams_are_interactive", lambda: True)
    monkeypatch.setattr("codegopher.tui.launch_tui", fake_launch_tui)

    result = CliRunner().invoke(app)

    assert result.exit_code == 0
    assert isinstance(captured["settings"], Settings)
    assert captured["cwd"] is not None


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


def test_cli_builds_real_openai_compatible_provider(monkeypatch) -> None:
    monkeypatch.delenv("CODEGOPHER_TEST_MOCK_RESPONSE", raising=False)
    monkeypatch.setenv("LOCAL_API_KEY", "sk-local")

    provider = cli_main._build_provider(
        Settings(
            model=ModelConfig(provider="openai", name="local-model"),
            providers={
                "openai": [
                    ProviderEntry(
                        id="local-model",
                        name="Local",
                        base_url="http://127.0.0.1:8000/v1",
                        api_key_env="LOCAL_API_KEY",
                    )
                ]
            },
        )
    )

    assert isinstance(provider, OpenAICompatProvider)
    assert provider.base_url == "http://127.0.0.1:8000/v1"
    assert provider.api_key == "sk-local"


def test_build_provider_honors_empty_environ(monkeypatch) -> None:
    monkeypatch.setenv("CODEGOPHER_TEST_MOCK_RESPONSE", "mocked")

    with pytest.raises(ProviderError, match="Missing API key"):
        build_provider(Settings(), environ={})
