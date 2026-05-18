from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from codegopher.cli.main import app
from codegopher.events.protocol import (
    SessionStartedEvent,
    TextDeltaEvent,
    TurnCompleteEvent,
    TurnStartedEvent,
    decode_jsonl_message,
)


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
