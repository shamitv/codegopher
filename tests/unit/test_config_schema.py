from __future__ import annotations

import pytest
from pydantic import ValidationError

from codegopher.config.schema import (
    ApprovalMode,
    McpTransport,
    ProviderApiFamily,
    ProviderEntry,
    Settings,
)


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
    assert settings.context.max_replay_messages is None
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
    assert settings.mcp.enabled is True
    assert settings.mcp.servers == {}
    assert settings.agent.max_iterations == 64


def test_settings_rejects_invalid_approval_mode() -> None:
    with pytest.raises(ValidationError):
        Settings.model_validate({"approval_mode": "sometimes"})


def test_settings_rejects_invalid_token_limit() -> None:
    with pytest.raises(ValidationError):
        Settings.model_validate({"model": {"max_output_tokens": 0}})


def test_settings_rejects_empty_model_name() -> None:
    with pytest.raises(ValidationError):
        Settings.model_validate({"model": {"name": ""}})


def test_provider_entry_defaults_to_chat_completions() -> None:
    settings = Settings.model_validate(
        {"providers": {"openai": [{"id": "gpt-test", "name": "GPT Test"}]}}
    )

    assert settings.providers["openai"][0].api_family is ProviderApiFamily.chat_completions
    assert settings.providers["openai"][0].replay_reasoning_content is False


def test_provider_entry_accepts_reasoning_replay_flag() -> None:
    entry = ProviderEntry(
        id="deepseek",
        name="DeepSeek",
        replay_reasoning_content=True,
    )

    assert entry.replay_reasoning_content is True


def test_provider_entry_rejects_invalid_api_family() -> None:
    with pytest.raises(ValidationError):
        Settings.model_validate(
            {
                "providers": {
                    "openai": [
                        {"id": "gpt-test", "name": "GPT Test", "api_family": "assistants"}
                    ]
                }
            }
        )


def test_mcp_config_accepts_stdio_and_sse_servers() -> None:
    settings = Settings.model_validate(
        {
            "mcp": {
                "servers": {
                    "local": {
                        "transport": "stdio",
                        "command": "npx",
                        "args": ["@playwright/mcp@latest"],
                    },
                    "remote": {
                        "transport": "sse",
                        "url": "https://example.test/sse",
                        "headers_env": {"Authorization": "MCP_AUTH"},
                    },
                }
            }
        }
    )

    assert settings.mcp.servers["local"].transport is McpTransport.stdio
    assert settings.mcp.servers["remote"].transport is McpTransport.sse
    assert settings.mcp.servers["remote"].headers_env == {"Authorization": "MCP_AUTH"}


def test_mcp_config_requires_transport_specific_fields() -> None:
    with pytest.raises(ValidationError, match="stdio MCP servers require command"):
        Settings.model_validate({"mcp": {"servers": {"local": {"transport": "stdio"}}}})

    with pytest.raises(ValidationError, match="sse MCP servers require url"):
        Settings.model_validate({"mcp": {"servers": {"remote": {"transport": "sse"}}}})


def test_disabled_mcp_server_can_omit_transport_fields() -> None:
    settings = Settings.model_validate(
        {"mcp": {"servers": {"future": {"enabled": False, "transport": "sse"}}}}
    )

    assert settings.mcp.servers["future"].enabled is False


def test_settings_rejects_invalid_context_threshold_order() -> None:
    with pytest.raises(ValidationError):
        Settings.model_validate(
            {"context": {"warning_threshold": 0.90, "compaction_threshold": 0.80}}
        )


def test_settings_rejects_invalid_context_threshold_bounds() -> None:
    with pytest.raises(ValidationError):
        Settings.model_validate({"context": {"warning_threshold": 0.0}})


def test_settings_rejects_invalid_context_replay_cap() -> None:
    with pytest.raises(ValidationError):
        Settings.model_validate({"context": {"max_replay_messages": 0}})


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


def test_settings_rejects_invalid_agent_limits() -> None:
    with pytest.raises(ValidationError):
        Settings.model_validate({"agent": {"max_iterations": 0}})
