"""Context token accounting helpers."""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import Any

from codegopher.config.schema import ProviderEntry, Settings
from codegopher.core.types import Message
from codegopher.utils.json import dumps_json

try:  # pragma: no cover - exercised through the public fallback path.
    import tiktoken
except Exception:  # pragma: no cover
    tiktoken = None  # type: ignore[assignment]


@dataclass(frozen=True)
class ContextBudgetStatus:
    token_count: int
    context_window: int | None
    warning_tokens: int | None
    compaction_tokens: int | None
    warning_exceeded: bool
    compaction_exceeded: bool
    usage_ratio: float | None


def count_text_tokens(text: str, *, encoding_name: str = "cl100k_base") -> int:
    """Count tokens for text, falling back to a deterministic byte estimate."""
    if not text:
        return 0
    if tiktoken is not None:
        try:
            return len(tiktoken.get_encoding(encoding_name).encode(text))
        except Exception:
            pass
    return _fallback_count(text)


def count_message_tokens(
    messages: list[Message],
    *,
    encoding_name: str = "cl100k_base",
) -> int:
    """Estimate provider message tokens using stable per-message overhead."""
    total = 0
    for message in messages:
        total += 4
        for key in ("role", "content", "name", "tool_call_id", "reasoning_content"):
            value = message.get(key)
            if isinstance(value, str):
                total += count_text_tokens(value, encoding_name=encoding_name)
        tool_calls: Any = message.get("tool_calls")
        if tool_calls is not None:
            total += count_text_tokens(dumps_json(tool_calls), encoding_name=encoding_name)
    return total


def selected_provider_entry(settings: Settings) -> ProviderEntry | None:
    """Return the provider entry selected by active provider/model settings."""
    entries = settings.providers.get(settings.model.provider, [])
    if not entries:
        return None
    return next((entry for entry in entries if entry.id == settings.model.name), entries[0])


def selected_context_window(settings: Settings) -> int | None:
    entry = selected_provider_entry(settings)
    return entry.context_window if entry else None


def evaluate_context_budget(
    token_count: int,
    *,
    settings: Settings,
) -> ContextBudgetStatus:
    context_window = selected_context_window(settings)
    if context_window is None:
        return ContextBudgetStatus(
            token_count=token_count,
            context_window=None,
            warning_tokens=None,
            compaction_tokens=None,
            warning_exceeded=False,
            compaction_exceeded=False,
            usage_ratio=None,
        )

    warning_tokens = max(1, ceil(context_window * settings.context.warning_threshold))
    compaction_tokens = max(1, ceil(context_window * settings.context.compaction_threshold))
    return ContextBudgetStatus(
        token_count=token_count,
        context_window=context_window,
        warning_tokens=warning_tokens,
        compaction_tokens=compaction_tokens,
        warning_exceeded=token_count >= warning_tokens,
        compaction_exceeded=token_count >= compaction_tokens,
        usage_ratio=token_count / context_window,
    )


def calculate_context_budget(
    messages: list[Message],
    *,
    settings: Settings,
    extra_tokens: int = 0,
) -> ContextBudgetStatus:
    token_count = count_message_tokens(
        messages,
        encoding_name=settings.context.token_encoding,
    )
    return evaluate_context_budget(token_count + extra_tokens, settings=settings)


def _fallback_count(text: str) -> int:
    return max(1, (len(text.encode("utf-8")) + 3) // 4)
