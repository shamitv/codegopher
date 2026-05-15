from __future__ import annotations

import pytest

from codegopher.providers.openai_compat import OpenAICompatProvider


def test_openai_compat_provider_resolves_api_key() -> None:
    provider = OpenAICompatProvider(environ={"OPENAI_API_KEY": "sk-test"}, client=object())

    assert provider.api_key == "sk-test"
    assert provider.api_key_env == "OPENAI_API_KEY"

