from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

import codegopher.cli.main as cli_main
from codegopher.cli.main import app
from codegopher.providers.mock import MockProvider


def test_headless_cli_denies_required_tool_when_non_tty(monkeypatch, tmp_path: Path) -> None:
    provider = MockProvider(
        [
            [
                {
                    "type": "tool_call",
                    "tool_call": {
                        "id": "call-1",
                        "name": "write_file",
                        "arguments": {"path": "new.txt", "content": "hello"},
                    },
                },
                {"type": "done"},
            ],
            [{"type": "text_delta", "content": "done"}, {"type": "done"}],
        ]
    )
    monkeypatch.setattr(cli_main, "_build_provider", lambda _settings: provider)

    with CliRunner().isolated_filesystem(temp_dir=tmp_path):
        result = CliRunner().invoke(app, ["-p", "write", "--json"])

    payload = json.loads(result.output)
    assert result.exit_code == 0
    assert payload["tool_results"][0]["is_error"] is True
    assert "stdin is not a TTY" in payload["tool_results"][0]["content"]


def test_headless_cli_yolo_allows_harmless_temp_write(monkeypatch, tmp_path: Path) -> None:
    provider = MockProvider(
        [
            [
                {
                    "type": "tool_call",
                    "tool_call": {
                        "id": "call-1",
                        "name": "list_dir",
                        "arguments": {"path": "."},
                    },
                },
                {"type": "done"},
            ],
            [
                {
                    "type": "tool_call",
                    "tool_call": {
                        "id": "call-2",
                        "name": "write_file",
                        "arguments": {"path": "new.txt", "content": "hello"},
                    },
                },
                {"type": "done"},
            ],
            [{"type": "text_delta", "content": "done"}, {"type": "done"}],
        ]
    )
    monkeypatch.setattr(cli_main, "_build_provider", lambda _settings: provider)

    with CliRunner().isolated_filesystem(temp_dir=tmp_path):
        result = CliRunner().invoke(app, ["-p", "write", "--approval-mode", "yolo", "--json"])
        written = Path("new.txt").read_text(encoding="utf-8")

    payload = json.loads(result.output)
    assert result.exit_code == 0
    assert written == "hello"
    assert [tool_result["is_error"] for tool_result in payload["tool_results"]] == [False, False]
