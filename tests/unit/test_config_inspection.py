from __future__ import annotations

from pathlib import Path

from codegopher.config.inspection import inspect_effective_config
from codegopher.config.loader import CliOverrides, load_settings, load_settings_with_metadata


def test_load_settings_with_metadata_preserves_existing_load_settings_behavior(
    tmp_path: Path,
) -> None:
    loaded = load_settings_with_metadata(cwd=tmp_path, home=tmp_path, environ={})
    settings = load_settings(cwd=tmp_path, home=tmp_path, environ={})

    assert loaded.settings == settings
    assert loaded.metadata.cwd == tmp_path
    assert loaded.metadata.home == tmp_path
    assert loaded.metadata.source_labels == ("defaults",)
    assert loaded.metadata.project_config_path == tmp_path / ".codegopher/settings.toml"


def test_inspect_effective_config_reports_defaults(tmp_path: Path) -> None:
    snapshot = inspect_effective_config(cwd=tmp_path, home=tmp_path, environ={})

    assert snapshot.workspace_root == str(tmp_path)
    assert snapshot.provider == "openai"
    assert snapshot.model == "gpt-4o"
    assert snapshot.provider_entry_id is None
    assert snapshot.provider_entry_name is None
    assert snapshot.api_family == "chat_completions"
    assert snapshot.base_url is None
    assert snapshot.config_sources == ("defaults",)


def test_inspect_effective_config_uses_selected_provider_entry(tmp_path: Path) -> None:
    home = tmp_path / "home"
    project = tmp_path / "project"
    home.mkdir()
    project.mkdir()
    config_dir = project / ".codegopher"
    config_dir.mkdir()
    (config_dir / "settings.toml").write_text(
        """
[model]
provider = "openai"
name = "gpt-selected"

[[providers.openai]]
id = "gpt-other"
name = "Other"
base_url = "https://other.example.test/v1"

[[providers.openai]]
id = "gpt-selected"
name = "Selected"
api_family = "responses"
base_url = "https://selected.example.test/v1"
""",
        encoding="utf-8",
    )

    snapshot = inspect_effective_config(cwd=project, home=home, environ={})

    assert snapshot.provider == "openai"
    assert snapshot.model == "gpt-selected"
    assert snapshot.provider_entry_id == "gpt-selected"
    assert snapshot.provider_entry_name == "Selected"
    assert snapshot.api_family == "responses"
    assert snapshot.base_url == "https://selected.example.test/v1"
    assert snapshot.config_sources == ("defaults", "project")


def test_inspect_effective_config_reports_user_project_env_and_cli_sources(
    tmp_path: Path,
) -> None:
    home = tmp_path / "home"
    project = tmp_path / "project"
    home_config = home / ".codegopher"
    project_config = project / ".codegopher"
    home_config.mkdir(parents=True)
    project_config.mkdir(parents=True)
    (home_config / "settings.toml").write_text(
        """
[model]
provider = "openai"
name = "user-model"

[[providers.openai]]
id = "user-model"
name = "User Model"
base_url = "https://user.example.test/v1"
""",
        encoding="utf-8",
    )
    (project_config / "settings.toml").write_text(
        """
[model]
name = "project-model"

[[providers.openai]]
id = "project-model"
name = "Project Model"
base_url = "https://project.example.test/v1"
""",
        encoding="utf-8",
    )

    snapshot = inspect_effective_config(
        cwd=project,
        home=home,
        environ={"CODEGOPHER_MODEL": "env-model"},
        cli_overrides=CliOverrides(
            model="cli-model",
            provider="openai",
            base_url="https://cli.example.test/v1",
            api_family="responses",
        ),
    )

    assert snapshot.provider == "openai"
    assert snapshot.model == "cli-model"
    assert snapshot.provider_entry_id == "cli-model"
    assert snapshot.provider_entry_name == "cli-model"
    assert snapshot.api_family == "responses"
    assert snapshot.base_url == "https://cli.example.test/v1"
    assert snapshot.config_sources == (
        "defaults",
        "user",
        "project",
        "environment",
        "cli",
    )


def test_inspect_effective_config_falls_back_to_first_provider_entry(
    tmp_path: Path,
) -> None:
    config_dir = tmp_path / ".codegopher"
    config_dir.mkdir()
    (config_dir / "settings.toml").write_text(
        """
[model]
provider = "openai"
name = "missing-model"

[[providers.openai]]
id = "fallback-model"
name = "Fallback"
base_url = "https://fallback.example.test/v1"
""",
        encoding="utf-8",
    )

    snapshot = inspect_effective_config(cwd=tmp_path, home=tmp_path / "home", environ={})

    assert snapshot.model == "missing-model"
    assert snapshot.provider_entry_id == "fallback-model"
    assert snapshot.provider_entry_name == "Fallback"
    assert snapshot.base_url == "https://fallback.example.test/v1"


def test_inspect_effective_config_does_not_expose_api_key_env(tmp_path: Path) -> None:
    config_dir = tmp_path / ".codegopher"
    config_dir.mkdir()
    (config_dir / "settings.toml").write_text(
        """
[model]
provider = "openai"
name = "gpt-test"

[[providers.openai]]
id = "gpt-test"
name = "GPT Test"
api_key_env = "OPENAI_API_KEY"
base_url = "https://api.example.test/v1"
""",
        encoding="utf-8",
    )

    snapshot = inspect_effective_config(cwd=tmp_path, home=tmp_path / "home", environ={})
    exposed = repr(snapshot)

    assert snapshot.base_url == "https://api.example.test/v1"
    assert "OPENAI_API_KEY" not in exposed
    assert "api_key_env" not in exposed
