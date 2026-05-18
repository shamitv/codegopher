from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

import codegopher.cli.main as cli_main
from codegopher.cli.main import app
from codegopher.config.schema import ModelConfig, ProviderEntry, Settings
from codegopher.core.agent import AgentResult
from codegopher.providers.mock import MockProvider
from codegopher.providers.openai_compat import OpenAICompatProvider
from codegopher.skills import discover_project_skills


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


def test_cli_debug_output_includes_reasoning(monkeypatch) -> None:
    provider = MockProvider(
        [
            [
                {"type": "reasoning_delta", "content": "thinking"},
                {"type": "text_delta", "content": "answer"},
                {"type": "done"},
            ]
        ]
    )
    monkeypatch.setattr(cli_main, "_build_provider", lambda _settings: provider)

    result = CliRunner().invoke(app, ["-p", "hello", "--debug"])

    assert result.exit_code == 0
    assert result.output == "Reasoning:\nthinking\nanswer\n"


def test_cli_json_debug_output_excludes_reasoning(monkeypatch) -> None:
    provider = MockProvider(
        [
            [
                {"type": "reasoning_delta", "content": "thinking"},
                {"type": "text_delta", "content": "answer"},
                {"type": "done"},
            ]
        ]
    )
    monkeypatch.setattr(cli_main, "_build_provider", lambda _settings: provider)

    result = CliRunner().invoke(app, ["-p", "hello", "--debug", "--json"])

    assert result.exit_code == 0
    assert json.loads(result.output)["final_text"] == "answer"
    assert "thinking" not in result.output


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


def test_cli_init_creates_default_project_skill(tmp_path: Path) -> None:
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(app, ["init"])
        skill_path = Path.cwd() / ".codegopher/skills/project/SKILL.md"

        assert result.exit_code == 0
        assert "Created" in result.output
        assert skill_path.exists()
        assert "# Project" in skill_path.read_text(encoding="utf-8")


def test_cli_init_supports_explicit_target_path(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.mkdir()

    result = CliRunner().invoke(app, ["init", str(target)])

    assert result.exit_code == 0
    assert (target / ".codegopher/skills/project/SKILL.md").exists()


def test_cli_init_skips_existing_skill_without_force(tmp_path: Path) -> None:
    skill_path = tmp_path / ".codegopher/skills/project/SKILL.md"
    skill_path.parent.mkdir(parents=True)
    skill_path.write_text("custom guidance", encoding="utf-8")

    result = CliRunner().invoke(app, ["init", str(tmp_path)])

    assert result.exit_code == 0
    assert "Skipped existing" in result.output
    assert skill_path.read_text(encoding="utf-8") == "custom guidance"


def test_cli_init_overwrites_existing_skill_with_force(tmp_path: Path) -> None:
    skill_path = tmp_path / ".codegopher/skills/project/SKILL.md"
    skill_path.parent.mkdir(parents=True)
    skill_path.write_text("custom guidance", encoding="utf-8")

    result = CliRunner().invoke(app, ["init", str(tmp_path), "--force"])

    assert result.exit_code == 0
    assert "Overwrote" in result.output
    assert "# Project" in skill_path.read_text(encoding="utf-8")


def test_cli_init_does_not_write_settings_or_secrets(tmp_path: Path) -> None:
    result = CliRunner().invoke(app, ["init", str(tmp_path)])

    raw = (tmp_path / ".codegopher/skills/project/SKILL.md").read_text(encoding="utf-8")
    assert result.exit_code == 0
    assert not (tmp_path / ".codegopher/settings.toml").exists()
    assert "api_key" not in raw.lower()
    assert "OPENAI_API_KEY" not in raw


def test_cli_init_generated_skill_is_discoverable(tmp_path: Path) -> None:
    result = CliRunner().invoke(app, ["init", str(tmp_path)])

    discovery = discover_project_skills(cwd=tmp_path, settings=Settings())
    skill = discovery.catalog.get("project")
    assert result.exit_code == 0
    assert discovery.warnings == ()
    assert skill is not None
    assert skill.metadata.name == "Project"


def test_cli_init_repo_docs_skill_pack_materializes_documentation_skills(
    tmp_path: Path,
) -> None:
    result = CliRunner().invoke(
        app,
        ["init", str(tmp_path), "--skill-pack", "repo-docs"],
    )

    assert result.exit_code == 0
    assert "repo-domain-docs" in result.output
    assert "repo-tech-docs" in result.output
    assert (tmp_path / ".codegopher/skills/repo-domain-docs/SKILL.md").exists()
    assert (tmp_path / ".codegopher/skills/repo-tech-docs/SKILL.md").exists()
    assert not (tmp_path / ".codegopher/skills/crud-owasp-static-audit/SKILL.md").exists()
    assert not (tmp_path / ".codegopher/skills/project/SKILL.md").exists()


def test_cli_init_security_skill_pack_materializes_static_audit_skill(
    tmp_path: Path,
) -> None:
    result = CliRunner().invoke(
        app,
        ["init", str(tmp_path), "--skill-pack", "security"],
    )

    skill_path = tmp_path / ".codegopher/skills/crud-owasp-static-audit/SKILL.md"
    assert result.exit_code == 0
    assert skill_path.exists()
    raw = skill_path.read_text(encoding="utf-8")
    assert "static-only" in raw.lower()
    assert "OWASP Top 10:2025" in raw


def test_cli_init_all_skill_pack_materializes_all_v0_5_skills(tmp_path: Path) -> None:
    result = CliRunner().invoke(app, ["init", str(tmp_path), "--skill-pack", "all"])

    assert result.exit_code == 0
    for skill_id in (
        "repo-domain-docs",
        "repo-tech-docs",
        "crud-owasp-static-audit",
    ):
        assert (tmp_path / ".codegopher" / "skills" / skill_id / "SKILL.md").exists()


def test_cli_init_skill_pack_skips_existing_files_without_force(tmp_path: Path) -> None:
    skill_path = tmp_path / ".codegopher/skills/repo-domain-docs/SKILL.md"
    skill_path.parent.mkdir(parents=True)
    skill_path.write_text("custom domain guidance", encoding="utf-8")

    result = CliRunner().invoke(
        app,
        ["init", str(tmp_path), "--skill-pack", "repo-docs"],
    )

    assert result.exit_code == 0
    assert "Skipped existing" in result.output
    assert skill_path.read_text(encoding="utf-8") == "custom domain guidance"
    assert (tmp_path / ".codegopher/skills/repo-tech-docs/SKILL.md").exists()


def test_cli_init_skill_pack_overwrites_existing_files_with_force(
    tmp_path: Path,
) -> None:
    skill_path = tmp_path / ".codegopher/skills/crud-owasp-static-audit/SKILL.md"
    skill_path.parent.mkdir(parents=True)
    skill_path.write_text("custom security guidance", encoding="utf-8")

    result = CliRunner().invoke(
        app,
        ["init", str(tmp_path), "--skill-pack", "security", "--force"],
    )

    raw = skill_path.read_text(encoding="utf-8")
    assert result.exit_code == 0
    assert "Overwrote" in result.output
    assert "CRUD OWASP Static Audit" in raw


def test_cli_init_skill_pack_does_not_write_settings_or_secrets(tmp_path: Path) -> None:
    result = CliRunner().invoke(app, ["init", str(tmp_path), "--skill-pack", "all"])
    raw = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted((tmp_path / ".codegopher/skills").glob("*/SKILL.md"))
    )

    assert result.exit_code == 0
    assert not (tmp_path / ".codegopher/settings.toml").exists()
    assert "api_key" not in raw.lower()
    assert "OPENAI_API_KEY" not in raw
