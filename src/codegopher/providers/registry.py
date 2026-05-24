"""Provider registry."""

from __future__ import annotations

from collections.abc import Callable, Mapping

from codegopher.config.schema import ProviderApiFamily
from codegopher.core.errors import ProviderError
from codegopher.providers.base import Provider
from codegopher.providers.openai_compat import OpenAICompatProvider
from codegopher.providers.openai_responses import OpenAIResponsesProvider

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


def create_provider_registry(
    *,
    environ: Mapping[str, str] | None = None,
    base_url: str | None = None,
    api_key_env: str | None = "OPENAI_API_KEY",
    api_family: ProviderApiFamily = ProviderApiFamily.chat_completions,
    replay_reasoning_content: bool = False,
) -> ProviderRegistry:
    registry = ProviderRegistry()
    if api_family is ProviderApiFamily.responses:
        registry.register(
            "openai",
            lambda: OpenAIResponsesProvider(
                base_url=base_url,
                api_key_env=api_key_env,
                environ=environ,
            ),
        )
        return registry
    registry.register(
        "openai",
        lambda: OpenAICompatProvider(
            base_url=base_url,
            api_key_env=api_key_env,
            environ=environ,
            replay_reasoning_content=replay_reasoning_content,
        ),
    )
    return registry
