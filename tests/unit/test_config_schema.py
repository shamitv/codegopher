from __future__ import annotations

from codegopher.config.schema import ApprovalMode, Settings


def test_settings_defaults() -> None:
    settings = Settings()

    assert settings.model.provider == "openai"
    assert settings.model.name == "gpt-4o"
    assert settings.model.max_output_tokens == 8192
    assert settings.approval_mode is ApprovalMode.review
    assert settings.ignore_file == ".codegopherignore"

