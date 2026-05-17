from __future__ import annotations

from codegopher.config.schema import ModelConfig, ProviderEntry, Settings
from codegopher.core import context_budget
from codegopher.core.context_budget import calculate_context_budget, count_message_tokens
from codegopher.core.context_budget import count_text_tokens, evaluate_context_budget
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


def test_evaluate_context_budget_calculates_warning_and_compaction_thresholds() -> None:
    settings = Settings(
        model=ModelConfig(provider="openai", name="test"),
        providers={"openai": [ProviderEntry(id="test", name="Test", context_window=100)]},
    )

    below = evaluate_context_budget(69, settings=settings)
    warning = evaluate_context_budget(70, settings=settings)
    compact = evaluate_context_budget(80, settings=settings)

    assert below.warning_tokens == 70
    assert below.compaction_tokens == 80
    assert below.warning_exceeded is False
    assert warning.warning_exceeded is True
    assert warning.compaction_exceeded is False
    assert compact.compaction_exceeded is True
    assert compact.usage_ratio == 0.8


def test_evaluate_context_budget_is_open_when_context_window_is_unknown() -> None:
    status = evaluate_context_budget(10_000, settings=Settings())

    assert status.context_window is None
    assert status.warning_tokens is None
    assert status.compaction_tokens is None
    assert status.warning_exceeded is False
    assert status.compaction_exceeded is False
    assert status.usage_ratio is None


def test_calculate_context_budget_counts_messages_and_extra_tokens(monkeypatch) -> None:
    monkeypatch.setattr(context_budget, "tiktoken", None)
    settings = Settings(
        model=ModelConfig(provider="openai", name="test"),
        providers={"openai": [ProviderEntry(id="test", name="Test", context_window=10)]},
    )

    status = calculate_context_budget(
        [{"role": "user", "content": "abcdefgh"}],
        settings=settings,
        extra_tokens=2,
    )

    assert status.token_count == 9
    assert status.warning_exceeded is True
    assert status.compaction_exceeded is True


def test_calculate_context_budget_still_counts_tokens_without_context_window(
    monkeypatch,
) -> None:
    monkeypatch.setattr(context_budget, "tiktoken", None)

    status = calculate_context_budget(
        [{"role": "user", "content": "abcdefgh"}],
        settings=Settings(),
    )

    assert status.token_count > 0
    assert status.context_window is None
    assert status.compaction_exceeded is False


def test_evaluate_context_budget_handles_one_token_context_window() -> None:
    settings = Settings(
        model=ModelConfig(provider="openai", name="tiny"),
        providers={"openai": [ProviderEntry(id="tiny", name="Tiny", context_window=1)]},
    )

    empty = evaluate_context_budget(0, settings=settings)
    full = evaluate_context_budget(1, settings=settings)

    assert empty.warning_tokens == 1
    assert empty.compaction_tokens == 1
    assert empty.warning_exceeded is False
    assert full.warning_exceeded is True
    assert full.compaction_exceeded is True


def test_evaluate_context_budget_handles_small_threshold_rounding() -> None:
    settings = Settings(
        model=ModelConfig(provider="openai", name="tiny"),
        providers={"openai": [ProviderEntry(id="tiny", name="Tiny", context_window=3)]},
    )

    status = evaluate_context_budget(2, settings=settings)

    assert status.warning_tokens == 3
    assert status.compaction_tokens == 3
    assert status.warning_exceeded is False
