from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

import codegopher.cli.main as cli_main
from codegopher.cli.main import app
from codegopher.config.schema import ModelConfig, ProviderApiFamily, ProviderEntry, Settings
from codegopher.core.agent import AgentResult
from codegopher.core.errors import ConfigurationError
from codegopher.providers.mock import MockProvider
from codegopher.providers.openai_compat import OpenAICompatProvider
from codegopher.providers.openai_responses import OpenAIResponsesProvider
from codegopher.skills import discover_project_skills


def test_cli_without_prompt_requires_interactive_tty(tmp_path: Path) -> None:
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(app)
        assert not (Path.cwd() / ".codegopher").exists()

    assert result.exit_code != 0
    assert "pass -p/--prompt for headless usage" in result.output


def test_cli_without_prompt_launches_tui_when_interactive(
    monkeypatch,
    tmp_path: Path,
) -> None:
    captured: dict[str, object] = {}

    def fake_launch_tui(settings: Settings, *, cwd) -> None:
        captured["settings"] = settings
        captured["cwd"] = cwd
        captured["project_skill_exists"] = (
            Path.cwd() / ".codegopher/skills/project/SKILL.md"
        ).exists()

    monkeypatch.setattr(cli_main, "_streams_are_interactive", lambda: True)
    monkeypatch.setattr("codegopher.tui.launch_tui", fake_launch_tui)

    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(app)

    assert result.exit_code == 0
    assert isinstance(captured["settings"], Settings)
    assert captured["cwd"] is not None
    assert captured["project_skill_exists"] is True


def test_cli_without_prompt_no_project_init_skips_tui_implicit_init(
    monkeypatch,
    tmp_path: Path,
) -> None:
    captured: dict[str, object] = {}

    def fake_launch_tui(settings: Settings, *, cwd) -> None:
        captured["settings"] = settings
        captured["cwd"] = cwd

    monkeypatch.setattr(cli_main, "_streams_are_interactive", lambda: True)
    monkeypatch.setattr("codegopher.tui.launch_tui", fake_launch_tui)

    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(app, ["--no-project-init"])
        assert not (Path.cwd() / ".codegopher").exists()

    assert result.exit_code == 0
    assert isinstance(captured["settings"], Settings)


def test_cli_prompt_dry_run_echoes_prompt() -> None:
    result = CliRunner().invoke(
        app,
        ["--no-project-init", "-p", "hello"],
        env={"CODEGOPHER_TEST_MOCK_RESPONSE": "mocked"},
    )

    assert result.exit_code == 0
    assert result.output == "mocked\n"


def test_cli_does_not_expose_public_benchmark_command() -> None:
    result = CliRunner().invoke(app, ["benchmark"])

    assert result.exit_code != 0
    assert "No such command 'benchmark'" in result.output


def test_cli_applies_settings_overrides() -> None:
    result = CliRunner().invoke(
        app,
        [
            "--no-project-init",
            "-p",
            "hello",
            "--model",
            "local-model",
            "--provider",
            "local",
        ],
        env={"CODEGOPHER_TEST_MOCK_RESPONSE": "mocked"},
    )

    assert result.exit_code == 0
    assert result.output == "mocked\n"


def test_cli_applies_api_family_override(monkeypatch) -> None:
    captured: dict[str, Settings] = {}

    async def fake_run_agent(**kwargs):
        captured["settings"] = kwargs["settings"]
        return AgentResult(final_text="ok", iterations=1)

    monkeypatch.setattr(cli_main, "run_agent", fake_run_agent)

    result = CliRunner().invoke(
        app,
        ["--no-project-init", "-p", "hello", "--api-family", "responses"],
        env={"CODEGOPHER_TEST_MOCK_RESPONSE": "unused"},
    )

    assert result.exit_code == 0
    assert captured["settings"].providers["openai"][0].api_family.value == "responses"


def test_cli_applies_reasoning_replay_override(monkeypatch) -> None:
    captured: dict[str, Settings] = {}

    async def fake_run_agent(**kwargs):
        captured["settings"] = kwargs["settings"]
        return AgentResult(final_text="ok", iterations=1)

    monkeypatch.setattr(cli_main, "run_agent", fake_run_agent)

    result = CliRunner().invoke(
        app,
        ["--no-project-init", "-p", "hello", "--replay-reasoning-content"],
        env={"CODEGOPHER_TEST_MOCK_RESPONSE": "unused"},
    )

    assert result.exit_code == 0
    assert captured["settings"].providers["openai"][0].replay_reasoning_content is True


def test_cli_applies_max_iterations_override(monkeypatch) -> None:
    captured: dict[str, Settings] = {}

    async def fake_run_agent(**kwargs):
        captured["settings"] = kwargs["settings"]
        return AgentResult(final_text="ok", iterations=1)

    monkeypatch.setattr(cli_main, "run_agent", fake_run_agent)

    result = CliRunner().invoke(
        app,
        ["--no-project-init", "-p", "hello", "--max-iterations", "24"],
        env={"CODEGOPHER_TEST_MOCK_RESPONSE": "unused"},
    )

    assert result.exit_code == 0
    assert captured["settings"].agent.max_iterations == 24


def test_cli_rejects_invalid_max_iterations() -> None:
    result = CliRunner().invoke(
        app,
        ["--no-project-init", "-p", "hello", "--max-iterations", "0"],
        env={"CODEGOPHER_TEST_MOCK_RESPONSE": "unused"},
    )

    assert result.exit_code != 0
    assert "Invalid value for '--max-iterations'" in result.output


def test_cli_appends_piped_stdin_to_prompt(monkeypatch) -> None:
    captured: dict[str, str] = {}

    async def fake_run_agent(**kwargs):
        captured["prompt"] = kwargs["prompt"]
        return AgentResult(final_text="ok", iterations=1)

    monkeypatch.setattr(cli_main, "run_agent", fake_run_agent)

    result = CliRunner().invoke(
        app,
        ["--no-project-init", "-p", "summarize"],
        input="log line\n",
        env={"CODEGOPHER_TEST_MOCK_RESPONSE": "unused"},
    )

    assert result.exit_code == 0
    assert captured["prompt"] == "summarize\n\nInput context:\nlog line\n"


def test_cli_json_output_shape_and_implicit_init(tmp_path: Path) -> None:
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(
            app,
            ["-p", "hello", "--json"],
            env={"CODEGOPHER_TEST_MOCK_RESPONSE": "mocked"},
        )
        project_skill = Path.cwd() / ".codegopher/skills/project/SKILL.md"

    assert result.exit_code == 0
    assert json.loads(result.output) == {
        "final_text": "mocked",
        "tool_results": [],
        "iterations": 1,
    }
    assert project_skill.exists()


def test_cli_events_prompt_routes_to_events_runner(monkeypatch, tmp_path: Path) -> None:
    captured: dict[str, object] = {}

    async def fake_run_events_cli(**kwargs) -> int:
        captured.update(kwargs)
        kwargs["stdout"].write("events-ok\n")
        return 0

    monkeypatch.setattr(cli_main, "run_events_cli", fake_run_events_cli)
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(
            app,
            ["--events", "-p", "hello", "--json"],
            env={"CODEGOPHER_TEST_MOCK_RESPONSE": "unused"},
        )
        project_skill = Path.cwd() / ".codegopher/skills/project/SKILL.md"

    assert result.exit_code == 0
    assert result.output == "events-ok\n"
    assert captured["prompt"] == "hello"
    assert isinstance(captured["settings"], Settings)
    assert captured["cwd"] is not None
    assert project_skill.exists()


def test_cli_headless_no_project_init_skips_implicit_init(tmp_path: Path) -> None:
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(
            app,
            ["--no-project-init", "-p", "hello"],
            env={"CODEGOPHER_TEST_MOCK_RESPONSE": "mocked"},
        )
        assert not (Path.cwd() / ".codegopher").exists()

    assert result.exit_code == 0
    assert result.output == "mocked\n"


def test_cli_existing_codegopher_directory_skips_implicit_init(tmp_path: Path) -> None:
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path):
        Path(".codegopher").mkdir()
        result = runner.invoke(
            app,
            ["-p", "hello"],
            env={"CODEGOPHER_TEST_MOCK_RESPONSE": "mocked"},
        )
        assert not (Path.cwd() / ".codegopher/skills/project/SKILL.md").exists()

    assert result.exit_code == 0
    assert result.output == "mocked\n"


def test_cli_implicit_init_failure_mentions_no_project_init(
    monkeypatch,
    tmp_path: Path,
) -> None:
    def fail_write(**kwargs) -> str:
        raise OSError("read-only")

    monkeypatch.setattr(cli_main, "_write_project_skill", fail_write)
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(
            app,
            ["-p", "hello"],
            env={"CODEGOPHER_TEST_MOCK_RESPONSE": "mocked"},
        )

    assert result.exit_code != 0
    assert "--no-project-init" in result.output


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

    result = CliRunner().invoke(app, ["--no-project-init", "-p", "hello", "--debug"])

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

    result = CliRunner().invoke(
        app,
        ["--no-project-init", "-p", "hello", "--debug", "--json"],
    )

    assert result.exit_code == 0
    assert json.loads(result.output)["final_text"] == "answer"
    assert "thinking" not in result.output


def test_cli_headless_starts_and_closes_mcp_registry(monkeypatch) -> None:
    events: list[str] = []
    captured: dict[str, object] = {}

    class FakeTool:
        name = "mcp__local__echo"
        description = "Echo"
        parameters = {"type": "object", "properties": {}}
        requires_approval = True

        async def execute(self, arguments, context):
            raise AssertionError("not used")

    class FakeMcpManager:
        def __init__(self, *, settings, cwd, environ) -> None:
            captured["cwd"] = cwd
            captured["settings"] = settings
            captured["has_environ"] = bool(environ)

        async def __aenter__(self):
            events.append("enter")
            return self

        async def __aexit__(self, *_exc_info):
            events.append("exit")

        def register_tools(self, registry) -> None:
            registry.register(FakeTool())

    async def fake_run_agent(**kwargs):
        captured["tool_names"] = [tool.name for tool in kwargs["registry"].list()]
        return AgentResult(final_text="ok", iterations=1)

    monkeypatch.setattr(cli_main, "McpManager", FakeMcpManager)
    monkeypatch.setattr(cli_main, "run_agent", fake_run_agent)

    result = CliRunner().invoke(
        app,
        ["--no-project-init", "-p", "hello"],
        env={"CODEGOPHER_TEST_MOCK_RESPONSE": "unused"},
    )

    assert result.exit_code == 0
    assert events == ["enter", "exit"]
    assert captured["has_environ"] is True
    assert "mcp__local__echo" in captured["tool_names"]


def test_cli_headless_reports_mcp_startup_failure(monkeypatch) -> None:
    class FakeMcpManager:
        def __init__(self, *, settings, cwd, environ) -> None:
            pass

        async def __aenter__(self):
            raise ConfigurationError("MCP server local failed to initialize")

        async def __aexit__(self, *_exc_info):
            pass

    monkeypatch.setattr(cli_main, "McpManager", FakeMcpManager)

    result = CliRunner().invoke(
        app,
        ["--no-project-init", "-p", "hello", "--json"],
        env={"CODEGOPHER_TEST_MOCK_RESPONSE": "mocked"},
    )

    assert result.exit_code != 0
    assert "MCP server local failed to initialize" in result.output
    assert not result.output.strip().startswith("{")


def test_cli_reports_configuration_errors() -> None:
    result = CliRunner().invoke(
        app,
        ["--no-project-init", "-p", "hello"],
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
        ["--no-project-init", "-p", "hello"],
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
                        replay_reasoning_content=True,
                    )
                ]
            },
        )
    )

    assert isinstance(provider, OpenAICompatProvider)
    assert provider.base_url == "http://127.0.0.1:8000/v1"
    assert provider.api_key == "sk-local"
    assert provider.replay_reasoning_content is True


def test_cli_builds_real_openai_responses_provider(monkeypatch) -> None:
    monkeypatch.delenv("CODEGOPHER_TEST_MOCK_RESPONSE", raising=False)
    monkeypatch.setenv("LOCAL_API_KEY", "sk-local")

    provider = cli_main._build_provider(
        Settings(
            model=ModelConfig(provider="openai", name="responses-model"),
            providers={
                "openai": [
                    ProviderEntry(
                        id="responses-model",
                        name="Responses",
                        api_key_env="LOCAL_API_KEY",
                        api_family=ProviderApiFamily.responses,
                    )
                ]
            },
        )
    )

    assert isinstance(provider, OpenAIResponsesProvider)
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
    chained_path = tmp_path / ".codegopher/skills/chained-vulnerability-static-audit/SKILL.md"
    assert result.exit_code == 0
    assert skill_path.exists()
    assert chained_path.exists()
    raw = skill_path.read_text(encoding="utf-8")
    assert "static-only" in raw.lower()
    assert "OWASP Top 10:2025" in raw
    assert "attack graph" in chained_path.read_text(encoding="utf-8").lower()


def test_cli_init_chained_vulns_skill_pack_materializes_only_chained_audit_skill(
    tmp_path: Path,
) -> None:
    result = CliRunner().invoke(
        app,
        ["init", str(tmp_path), "--skill-pack", "chained-vulns"],
    )

    assert result.exit_code == 0
    assert (tmp_path / ".codegopher/skills/chained-vulnerability-static-audit/SKILL.md").exists()
    assert not (tmp_path / ".codegopher/skills/crud-owasp-static-audit/SKILL.md").exists()
    assert not (tmp_path / ".codegopher/skills/repo-domain-docs/SKILL.md").exists()


def test_cli_init_all_skill_pack_materializes_all_v0_5_skills(tmp_path: Path) -> None:
    result = CliRunner().invoke(app, ["init", str(tmp_path), "--skill-pack", "all"])

    assert result.exit_code == 0
    for skill_id in (
        "repo-domain-docs",
        "repo-tech-docs",
        "crud-owasp-static-audit",
        "chained-vulnerability-static-audit",
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
