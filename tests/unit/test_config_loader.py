from __future__ import annotations

from pathlib import Path

import pytest

from codegopher.config.loader import CliOverrides, load_settings, load_settings_with_metadata
from codegopher.core.errors import ConfigurationError


def test_load_settings_returns_defaults(tmp_path: Path) -> None:
    settings = load_settings(cwd=tmp_path, home=tmp_path, environ={})

    assert settings.model.provider == "openai"
    assert settings.approval_mode.value == "review"
    assert settings.agent.max_iterations == 64


def test_load_settings_reads_user_toml(tmp_path: Path) -> None:
    config_dir = tmp_path / ".codegopher"
    config_dir.mkdir()
    project = tmp_path / "project"
    project.mkdir()
    (config_dir / "settings.toml").write_text(
        '[model]\nname = "user-model"\n',
        encoding="utf-8",
    )

    settings = load_settings(cwd=project, home=tmp_path, environ={})

    assert settings.model.name == "user-model"


def test_load_settings_reads_project_toml(tmp_path: Path) -> None:
    project = tmp_path / "project"
    config_dir = project / ".codegopher"
    config_dir.mkdir(parents=True)
    (config_dir / "settings.toml").write_text(
        'approval_mode = "auto"\n',
        encoding="utf-8",
    )

    settings = load_settings(cwd=project, home=tmp_path, environ={})

    assert settings.approval_mode.value == "auto"


def test_load_settings_merges_nested_config_deterministically(tmp_path: Path) -> None:
    user_config = tmp_path / ".codegopher"
    user_config.mkdir()
    (user_config / "settings.toml").write_text(
        '[model]\nprovider = "openai"\nname = "user-model"\ntemperature = 0.4\n',
        encoding="utf-8",
    )
    project = tmp_path / "project"
    project_config = project / ".codegopher"
    project_config.mkdir(parents=True)
    (project_config / "settings.toml").write_text(
        '[model]\nname = "project-model"\n',
        encoding="utf-8",
    )

    settings = load_settings(cwd=project, home=tmp_path, environ={})

    assert settings.model.provider == "openai"
    assert settings.model.name == "project-model"
    assert settings.model.temperature == 0.4


def test_load_settings_applies_environment_overrides(tmp_path: Path) -> None:
    settings = load_settings(
        cwd=tmp_path,
        home=tmp_path,
        environ={
            "CODEGOPHER_MODEL": "env-model",
            "CODEGOPHER_PROVIDER": "local",
            "CODEGOPHER_APPROVAL_MODE": "yolo",
            "CODEGOPHER_BASE_URL": "http://127.0.0.1:8000/v1",
            "CODEGOPHER_API_KEY_ENV": "LOCAL_API_KEY",
            "CODEGOPHER_API_FAMILY": "responses",
            "CODEGOPHER_REPLAY_REASONING_CONTENT": "true",
            "CODEGOPHER_MAX_OUTPUT_TOKENS": "16384",
            "CODEGOPHER_DEBUG": "true",
        },
    )

    assert settings.model.provider == "local"
    assert settings.model.name == "env-model"
    assert settings.approval_mode.value == "yolo"
    assert settings.debug is True
    assert settings.providers["local"][0].base_url == "http://127.0.0.1:8000/v1"
    assert settings.providers["local"][0].api_key_env == "LOCAL_API_KEY"
    assert settings.providers["local"][0].api_family.value == "responses"
    assert settings.providers["local"][0].replay_reasoning_content is True
    assert settings.model.max_output_tokens == 16384


def test_load_settings_applies_cli_overrides_after_environment(tmp_path: Path) -> None:
    settings = load_settings(
        cwd=tmp_path,
        home=tmp_path,
        environ={"CODEGOPHER_MODEL": "env-model"},
        cli_overrides=CliOverrides(
            model="cli-model",
            provider="openai",
            base_url="http://localhost:8000/v1",
            api_family="responses",
            replay_reasoning_content=True,
            approval_mode="auto",
            max_iterations=24,
            max_output_tokens=12288,
            debug=True,
        ),
    )

    assert settings.model.name == "cli-model"
    assert settings.model.provider == "openai"
    assert settings.approval_mode.value == "auto"
    assert settings.agent.max_iterations == 24
    assert settings.model.max_output_tokens == 12288
    assert settings.debug is True
    assert settings.providers["openai"][0].base_url == "http://localhost:8000/v1"
    assert settings.providers["openai"][0].api_family.value == "responses"
    assert settings.providers["openai"][0].replay_reasoning_content is True


def test_load_settings_preserves_env_api_key_env_with_cli_endpoint_overrides(tmp_path: Path) -> None:
    settings = load_settings(
        cwd=tmp_path,
        home=tmp_path,
        environ={"CODEGOPHER_API_KEY_ENV": "LOCAL_API_KEY"},
        cli_overrides=CliOverrides(
            model="local-model",
            base_url="http://localhost:8000/v1",
            api_family="chat_completions",
        ),
    )

    assert settings.model.name == "local-model"
    assert settings.providers["openai"][0].base_url == "http://localhost:8000/v1"
    assert settings.providers["openai"][0].api_key_env == "LOCAL_API_KEY"
    assert settings.providers["openai"][0].api_family.value == "chat_completions"


def test_load_settings_applies_cli_endpoint_overrides_to_env_provider(tmp_path: Path) -> None:
    settings = load_settings(
        cwd=tmp_path,
        home=tmp_path,
        environ={"CODEGOPHER_PROVIDER": "local"},
        cli_overrides=CliOverrides(
            model="local-model",
            base_url="http://localhost:8000/v1",
            api_family="chat_completions",
        ),
    )

    assert settings.model.provider == "local"
    assert settings.model.name == "local-model"
    assert "openai" not in settings.providers
    assert settings.providers["local"][0].id == "local-model"
    assert settings.providers["local"][0].base_url == "http://localhost:8000/v1"
    assert settings.providers["local"][0].api_family.value == "chat_completions"


def test_load_settings_preserves_env_api_key_when_cli_provider_wins(tmp_path: Path) -> None:
    settings = load_settings(
        cwd=tmp_path,
        home=tmp_path,
        environ={
            "CODEGOPHER_PROVIDER": "local",
            "CODEGOPHER_API_KEY_ENV": "LOCAL_API_KEY",
        },
        cli_overrides=CliOverrides(
            provider="openai",
            model="gpt-cli",
            base_url="http://localhost:8000/v1",
        ),
    )

    assert settings.model.provider == "openai"
    assert settings.model.name == "gpt-cli"
    assert "local" not in settings.providers
    assert settings.providers["openai"][0].id == "gpt-cli"
    assert settings.providers["openai"][0].base_url == "http://localhost:8000/v1"
    assert settings.providers["openai"][0].api_key_env == "LOCAL_API_KEY"


def test_load_settings_labels_env_only_api_key_env_source(tmp_path: Path) -> None:
    loaded = load_settings_with_metadata(
        cwd=tmp_path,
        home=tmp_path,
        environ={"CODEGOPHER_API_KEY_ENV": "LOCAL_API_KEY"},
    )

    assert loaded.metadata.source_labels == ("defaults", "environment")
    assert loaded.settings.providers["openai"][0].api_key_env == "LOCAL_API_KEY"


def test_load_settings_reports_malformed_toml_source(tmp_path: Path) -> None:
    config_dir = tmp_path / ".codegopher"
    config_dir.mkdir()
    path = config_dir / "settings.toml"
    path.write_text("[model\n", encoding="utf-8")

    with pytest.raises(ConfigurationError, match="Invalid TOML"):
        load_settings(cwd=tmp_path, home=tmp_path, environ={})
