from __future__ import annotations

from codegopher.core import context_budget
from codegopher.core.context_budget import count_message_tokens, count_text_tokens


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
