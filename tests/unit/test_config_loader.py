from __future__ import annotations

from pathlib import Path

import pytest

from codegopher.core.errors import ConfigurationError
from codegopher.config.loader import CliOverrides, load_settings


def test_load_settings_returns_defaults() -> None:
    settings = load_settings()

    assert settings.model.provider == "openai"
    assert settings.approval_mode.value == "review"


def test_load_settings_reads_user_toml(tmp_path: Path) -> None:
    config_dir = tmp_path / ".codegopher"
    config_dir.mkdir()
    (config_dir / "settings.toml").write_text(
        '[model]\nname = "user-model"\n',
        encoding="utf-8",
    )

    settings = load_settings(home=tmp_path)

    assert settings.model.name == "user-model"


def test_load_settings_reads_project_toml(tmp_path: Path) -> None:
    project = tmp_path / "project"
    config_dir = project / ".codegopher"
    config_dir.mkdir(parents=True)
    (config_dir / "settings.toml").write_text(
        'approval_mode = "auto"\n',
        encoding="utf-8",
    )

    settings = load_settings(cwd=project, home=tmp_path)

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

    settings = load_settings(cwd=project, home=tmp_path)

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
            "CODEGOPHER_DEBUG": "true",
        },
    )

    assert settings.model.provider == "local"
    assert settings.model.name == "env-model"
    assert settings.approval_mode.value == "yolo"
    assert settings.debug is True
    assert settings.providers["local"][0].base_url == "http://127.0.0.1:8000/v1"
    assert settings.providers["local"][0].api_key_env == "LOCAL_API_KEY"


def test_load_settings_applies_cli_overrides_after_environment(tmp_path: Path) -> None:
    settings = load_settings(
        cwd=tmp_path,
        home=tmp_path,
        environ={"CODEGOPHER_MODEL": "env-model"},
        cli_overrides=CliOverrides(
            model="cli-model",
            provider="openai",
            base_url="http://localhost:8000/v1",
            approval_mode="auto",
            debug=True,
        ),
    )

    assert settings.model.name == "cli-model"
    assert settings.model.provider == "openai"
    assert settings.approval_mode.value == "auto"
    assert settings.debug is True
    assert settings.providers["openai"][0].base_url == "http://localhost:8000/v1"


def test_load_settings_reports_malformed_toml_source(tmp_path: Path) -> None:
    config_dir = tmp_path / ".codegopher"
    config_dir.mkdir()
    path = config_dir / "settings.toml"
    path.write_text("[model\n", encoding="utf-8")

    with pytest.raises(ConfigurationError, match="Invalid TOML"):
        load_settings(cwd=tmp_path, home=tmp_path)
