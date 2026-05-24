from __future__ import annotations

import json
import os
from pathlib import Path

from click.testing import CliRunner

from codegopher.cli.main import app

LOCAL_LLM_BASE_URL = "http://192.168.96.5:8080/v1"
LOCAL_LLM_MODEL = "Qwen/Qwen3.6-35B-A3B"


def test_real_openai_compatible_endpoint_smoke() -> None:
    env = dict(os.environ)
    env.pop("CODEGOPHER_TEST_MOCK_RESPONSE", None)
    env["OPENAI_API_KEY"] = "dummy-key"

    result = CliRunner().invoke(
        app,
        [
            "--no-project-init",
            "-p",
            "Reply with exactly: codegopher-smoke-ok",
            "--model",
            LOCAL_LLM_MODEL,
            "--base-url",
            LOCAL_LLM_BASE_URL,
            "--api-family",
            "chat_completions",
            "--json",
        ],
        env=env,
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["final_text"].strip() == "codegopher-smoke-ok"
    assert payload["tool_results"] == []
    assert payload["iterations"] == 1


def test_real_openai_compatible_endpoint_replays_reasoning_content_for_tool_loop(
    tmp_path: Path,
) -> None:
    env = dict(os.environ)
    env.pop("CODEGOPHER_TEST_MOCK_RESPONSE", None)
    env["OPENAI_API_KEY"] = "dummy-key"

    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        Path("marker.txt").write_text(
            "marker content for replay smoke\n",
            encoding="utf-8",
        )
        result = runner.invoke(
            app,
            [
                "--no-project-init",
                "-p",
                "Use the read_file tool to read marker.txt, then reply exactly: codegopher-replay-ok",
                "--model",
                LOCAL_LLM_MODEL,
                "--base-url",
                LOCAL_LLM_BASE_URL,
                "--api-family",
                "chat_completions",
                "--replay-reasoning-content",
                "--approval-mode",
                "yolo",
                "--max-iterations",
                "4",
                "--json",
            ],
            env=env,
            catch_exceptions=False,
        )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["final_text"].strip() == "codegopher-replay-ok"
    assert payload["tool_results"]
    assert payload["iterations"] >= 2
