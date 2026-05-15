from __future__ import annotations

from pathlib import Path

from codegopher.config.loader import load_settings


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
