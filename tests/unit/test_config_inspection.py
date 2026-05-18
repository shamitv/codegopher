from __future__ import annotations

from pathlib import Path

from codegopher.config.inspection import inspect_effective_config
from codegopher.config.loader import load_settings, load_settings_with_metadata


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
