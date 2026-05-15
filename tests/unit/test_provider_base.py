from __future__ import annotations

from codegopher.providers.base import ProviderCapabilities


def test_provider_capabilities_defaults_token_counting_false() -> None:
    capabilities = ProviderCapabilities(streaming=True, tool_calls=True)

    assert capabilities.streaming is True
    assert capabilities.tool_calls is True
    assert capabilities.token_counting is False

