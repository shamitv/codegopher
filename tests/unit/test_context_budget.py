from __future__ import annotations

from codegopher.config.schema import ModelConfig, ProviderEntry, Settings
from codegopher.core import context_budget
from codegopher.core.context_budget import count_message_tokens, count_text_tokens
from codegopher.core.context_budget import selected_context_window, selected_provider_entry


def test_count_text_tokens_uses_tiktoken_encoding() -> None:
    assert count_text_tokens("hello world", encoding_name="cl100k_base") == 2


def test_count_text_tokens_uses_deterministic_fallback(monkeypatch) -> None:
    monkeypatch.setattr(context_budget, "tiktoken", None)

    assert count_text_tokens("abcdefgh") == 2
    assert count_text_tokens("") == 0


def test_count_message_tokens_counts_message_fields_and_tool_calls(monkeypatch) -> None:
    monkeypatch.setattr(context_budget, "tiktoken", None)

    total = count_message_tokens(
        [
            {"role": "user", "content": "abcd"},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call-1",
                        "type": "function",
                        "function": {"name": "read_file", "arguments": "{}"},
                    }
                ],
            },
            {"role": "tool", "tool_call_id": "call-1", "content": "result"},
        ]
    )

    assert total > 12


def test_selected_context_window_uses_active_provider_and_model() -> None:
    settings = Settings(
        model=ModelConfig(provider="openai", name="large"),
        providers={
            "openai": [
                ProviderEntry(id="small", name="Small", context_window=1024),
                ProviderEntry(id="large", name="Large", context_window=8192),
            ]
        },
    )

    assert selected_context_window(settings) == 8192


def test_selected_context_window_falls_back_to_first_provider_entry() -> None:
    settings = Settings(
        model=ModelConfig(provider="openai", name="missing"),
        providers={"openai": [ProviderEntry(id="small", name="Small", context_window=1024)]},
    )

    assert selected_provider_entry(settings).id == "small"
    assert selected_context_window(settings) == 1024


def test_selected_context_window_returns_none_when_missing() -> None:
    assert selected_context_window(Settings()) is None
