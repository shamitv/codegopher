"""Runtime helpers shared by the CLI and TUI."""

from __future__ import annotations

import os
from collections.abc import Mapping

from codegopher.config.schema import Settings
from codegopher.providers.base import Provider
from codegopher.providers.mock import MockProvider
from codegopher.providers.registry import create_provider_registry


def build_provider(
    settings: Settings,
    *,
    environ: Mapping[str, str] | None = None,
) -> Provider:
    env = os.environ if environ is None else environ
    mock_response = env.get("CODEGOPHER_TEST_MOCK_RESPONSE")
    if mock_response is not None:
        return MockProvider([[{"type": "text_delta", "content": mock_response}, {"type": "done"}]])

    entries = settings.providers.get(settings.model.provider, [])
    selected = next((entry for entry in entries if entry.id == settings.model.name), None)
    if selected is None and entries:
        selected = entries[0]
    base_url = selected.base_url if selected else None
    api_key_env = selected.api_key_env if selected and selected.api_key_env else "OPENAI_API_KEY"
    return create_provider_registry(
        environ=env,
        base_url=base_url,
        api_key_env=api_key_env,
    ).create(settings.model.provider)
