"""Context token accounting helpers."""

from __future__ import annotations

from typing import Any

from codegopher.config.schema import ProviderEntry, Settings
from codegopher.core.types import Message
from codegopher.utils.json import dumps_json

try:  # pragma: no cover - exercised through the public fallback path.
    import tiktoken
except Exception:  # pragma: no cover
    tiktoken = None  # type: ignore[assignment]


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
        for key in ("role", "content", "name", "tool_call_id"):
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


def _fallback_count(text: str) -> int:
    return max(1, (len(text.encode("utf-8")) + 3) // 4)
