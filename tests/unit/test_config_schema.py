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
    assert settings.context.warning_threshold == 0.70
    assert settings.context.compaction_threshold == 0.80
    assert settings.context.token_encoding == "cl100k_base"
    assert settings.memory.enabled is True
    assert settings.memory.session_enabled is True
    assert settings.memory.project_enabled is True
    assert settings.memory.max_entries_per_scope == 200
    assert settings.memory.max_entry_chars == 4000
    assert settings.skills.enabled is True
    assert settings.skills.project_dir == ".codegopher/skills"
    assert settings.skills.user_dir == "skills"
    assert settings.skills.builtins_enabled is True
    assert settings.skills.autoload is True
    assert settings.todo.enabled is True
    assert settings.todo.max_items == 100


def test_settings_rejects_invalid_approval_mode() -> None:
    with pytest.raises(ValidationError):
        Settings.model_validate({"approval_mode": "sometimes"})


def test_settings_rejects_invalid_token_limit() -> None:
    with pytest.raises(ValidationError):
        Settings.model_validate({"model": {"max_output_tokens": 0}})


def test_settings_rejects_empty_model_name() -> None:
    with pytest.raises(ValidationError):
        Settings.model_validate({"model": {"name": ""}})


def test_settings_rejects_invalid_context_threshold_order() -> None:
    with pytest.raises(ValidationError):
        Settings.model_validate(
            {"context": {"warning_threshold": 0.90, "compaction_threshold": 0.80}}
        )


def test_settings_rejects_invalid_context_threshold_bounds() -> None:
    with pytest.raises(ValidationError):
        Settings.model_validate({"context": {"warning_threshold": 0.0}})


def test_settings_rejects_invalid_memory_limits() -> None:
    with pytest.raises(ValidationError):
        Settings.model_validate({"memory": {"max_entries_per_scope": 0}})

    with pytest.raises(ValidationError):
        Settings.model_validate({"memory": {"max_entry_chars": 0}})


def test_settings_rejects_empty_skill_paths() -> None:
    with pytest.raises(ValidationError):
        Settings.model_validate({"skills": {"project_dir": ""}})

    with pytest.raises(ValidationError):
        Settings.model_validate({"skills": {"user_dir": ""}})


def test_settings_rejects_invalid_todo_limits() -> None:
    with pytest.raises(ValidationError):
        Settings.model_validate({"todo": {"max_items": 0}})
