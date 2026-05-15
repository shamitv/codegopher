from __future__ import annotations

from codegopher.config.loader import load_settings


def test_load_settings_returns_defaults() -> None:
    settings = load_settings()

    assert settings.model.provider == "openai"
    assert settings.approval_mode.value == "review"

