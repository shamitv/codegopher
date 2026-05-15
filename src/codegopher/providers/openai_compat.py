"""OpenAI-compatible streaming provider."""

from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Any

from openai import AsyncOpenAI

from codegopher.core.errors import ProviderError
from codegopher.providers.base import ProviderCapabilities


class OpenAICompatProvider:
    capabilities = ProviderCapabilities(streaming=True, tool_calls=True, token_counting=True)

    def __init__(
        self,
        *,
        base_url: str | None = None,
        api_key_env: str | None = "OPENAI_API_KEY",
        environ: Mapping[str, str] | None = None,
        client: Any | None = None,
    ) -> None:
        env = environ or os.environ
        self.api_key_env = api_key_env or "OPENAI_API_KEY"
        self.api_key = env.get(self.api_key_env)
        if not self.api_key:
            raise ProviderError(f"Missing API key: expected environment variable {self.api_key_env}")
        self.base_url = base_url
        self._client = client or AsyncOpenAI(api_key=self.api_key, base_url=base_url)

