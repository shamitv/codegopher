from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from click.testing import CliRunner

from codegopher.cli.main import app
from codegopher.config.loader import load_settings


def test_real_openai_compatible_endpoint_smoke() -> None:
    if os.environ.get("CODEGOPHER_RUN_REAL_LLM") != "1":
        pytest.skip("set CODEGOPHER_RUN_REAL_LLM=1 to run the real endpoint smoke")

    env = dict(os.environ)
    env.pop("CODEGOPHER_TEST_MOCK_RESPONSE", None)
    env.setdefault("OPENAI_API_KEY", "dummy-key")
    settings = load_settings(cwd=Path.cwd(), environ=env)
    provider_entries = settings.providers.get(settings.model.provider, [])
    selected = next(
        (entry for entry in provider_entries if entry.id == settings.model.name),
        provider_entries[0] if provider_entries else None,
    )
    assert selected is not None
    assert selected.base_url is not None

    result = CliRunner().invoke(
        app,
        ["-p", "Reply with exactly: codegopher-smoke-ok", "--json"],
        env=env,
    )

    assert result.exit_code == 0, result.output
    assert json.loads(result.output) == {
        "final_text": "codegopher-smoke-ok",
        "tool_results": [],
        "iterations": 1,
    }
