from __future__ import annotations

import pytest
from pydantic import ValidationError

from codegopher.config.schema import ApprovalMode, Settings


def test_settings_defaults() -> None:
    settings = Settings()

    assert settings.model.provider == "openai"
    assert settings.model.name == "gpt-4o"
    assert settings.model.max_output_tokens == 8192
    assert settings.approval_mode is ApprovalMode.review
    assert settings.ignore_file == ".codegopherignore"


def test_settings_rejects_invalid_approval_mode() -> None:
    with pytest.raises(ValidationError):
        Settings.model_validate({"approval_mode": "sometimes"})


def test_settings_rejects_invalid_token_limit() -> None:
    with pytest.raises(ValidationError):
        Settings.model_validate({"model": {"max_output_tokens": 0}})


def test_settings_rejects_empty_model_name() -> None:
    with pytest.raises(ValidationError):
        Settings.model_validate({"model": {"name": ""}})
