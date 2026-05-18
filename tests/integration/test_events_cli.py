from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

import codegopher.cli.main as cli_main
from codegopher.cli.main import app
from codegopher.events.protocol import (
    ReasoningDeltaEvent,
    SessionStartedEvent,
    TextDeltaEvent,
    ToolCallEvent,
    ToolResultEvent,
    TurnCompleteEvent,
    TurnStartedEvent,
    decode_jsonl_message,
)
from codegopher.providers.mock import MockProvider


def decode_output(output: str):
    return [decode_jsonl_message(line) for line in output.splitlines()]


def test_events_cli_one_shot_emits_jsonl_text_response(tmp_path: Path) -> None:
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(
            app,
            ["--events", "--no-project-init", "-p", "hello"],
            env={"CODEGOPHER_TEST_MOCK_RESPONSE": "mocked"},
        )

    messages = decode_output(result.output)

    assert result.exit_code == 0
    assert [type(message) for message in messages] == [
        SessionStartedEvent,
        TurnStartedEvent,
        TextDeltaEvent,
        TurnCompleteEvent,
    ]
    assert messages[2].content == "mocked"
    assert messages[3].final_text == "mocked"


def test_events_cli_one_shot_emits_reasoning_without_final_text(
    monkeypatch,
    tmp_path: Path,
) -> None:
    provider = MockProvider(
        [
            [
                {"type": "reasoning_delta", "content": "private reasoning"},
                {"type": "text_delta", "content": "public answer"},
                {"type": "done"},
            ]
        ]
    )
    monkeypatch.setattr(cli_main, "_build_provider", lambda _settings: provider)
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(
            app,
            ["--events", "--no-project-init", "-p", "think"],
        )

    messages = decode_output(result.output)

    assert result.exit_code == 0
    assert any(isinstance(message, ReasoningDeltaEvent) for message in messages)
    assert any(
        isinstance(message, TextDeltaEvent) and message.content == "public answer"
        for message in messages
    )
    complete = next(message for message in messages if isinstance(message, TurnCompleteEvent))
    assert complete.final_text == "public answer"
    assert "private reasoning" not in complete.final_text


def test_events_cli_one_shot_emits_tool_call_and_result_events(
    monkeypatch,
    tmp_path: Path,
) -> None:
    provider = MockProvider(
        [
            [
                {
                    "type": "tool_call",
                    "tool_call": {
                        "id": "call-1",
                        "name": "read_file",
                        "arguments": {"path": "README.md"},
                    },
                },
                {"type": "done"},
            ],
            [{"type": "text_delta", "content": "read complete"}, {"type": "done"}],
        ]
    )
    monkeypatch.setattr(cli_main, "_build_provider", lambda _settings: provider)
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path):
        Path("README.md").write_text("project notes", encoding="utf-8")
        result = runner.invoke(
            app,
            ["--events", "--no-project-init", "-p", "read"],
        )

    messages = decode_output(result.output)
    tool_call = next(message for message in messages if isinstance(message, ToolCallEvent))
    tool_result = next(message for message in messages if isinstance(message, ToolResultEvent))
    complete = next(message for message in messages if isinstance(message, TurnCompleteEvent))

    assert result.exit_code == 0
    assert tool_call.tool_name == "read_file"
    assert "README.md" in tool_call.arguments_summary
    assert tool_result.tool_id == "call-1"
    assert tool_result.result_summary == "project notes"
    assert complete.final_text == "read complete"
    assert complete.tool_count == 1
