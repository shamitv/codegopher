"""Provider registry."""

from __future__ import annotations

from collections.abc import Callable

from codegopher.core.errors import ProviderError
from codegopher.providers.base import Provider


ProviderFactory = Callable[[], Provider]


class ProviderRegistry:
    def __init__(self) -> None:
        self._factories: dict[str, ProviderFactory] = {}

    def register(self, name: str, factory: ProviderFactory) -> None:
        self._factories[name] = factory

    def create(self, name: str, *, require_tool_calls: bool = True) -> Provider:
        try:
            provider = self._factories[name]()
        except KeyError as exc:
            raise ProviderError(f"Unknown provider: {name}") from exc
        if require_tool_calls and not provider.capabilities.tool_calls:
            raise ProviderError(f"Provider {name} does not support tool calls")
        return provider


def create_provider_registry() -> ProviderRegistry:
    return ProviderRegistry()

