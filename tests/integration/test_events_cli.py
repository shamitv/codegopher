from __future__ import annotations

import asyncio
from pathlib import Path

from click.testing import CliRunner

import codegopher.cli.main as cli_main
import codegopher.events.session as events_session_module
from codegopher.cli.main import app
from codegopher.events.cli import protocol_error
from codegopher.events.protocol import (
    ApprovalRequestEvent,
    ApprovalResponseCommand,
    CancelTurnCommand,
    ConfigSnapshotEvent,
    DeleteMcpServerCommand,
    ErrorEvent,
    GetEffectiveConfigCommand,
    ListMcpServersCommand,
    McpServerDeletedEvent,
    McpServerPayload,
    McpServerSavedEvent,
    McpServersEvent,
    ReasoningDeltaEvent,
    SaveMcpServerCommand,
    SessionStartedEvent,
    SetMcpServerEnabledCommand,
    ShutdownCommand,
    StartTurnCommand,
    TextDeltaEvent,
    ToolCallEvent,
    ToolResultEvent,
    TurnCompleteEvent,
    TurnStartedEvent,
    decode_jsonl_message,
)
from codegopher.events.session import turn_cancelled
from codegopher.providers.base import ProviderCapabilities
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


def test_events_cli_one_shot_accepts_approval_response_from_stdin(
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
                        "name": "write_file",
                        "arguments": {"path": "new.txt", "content": "hello"},
                    },
                },
                {"type": "done"},
            ],
            [{"type": "text_delta", "content": "denied"}, {"type": "done"}],
        ]
    )
    uuid_values = iter(["session0000", "turn0000000", "approval0000"])

    class FakeUuid:
        def __init__(self, value: str) -> None:
            self.hex = value

    monkeypatch.setattr(cli_main, "_build_provider", lambda _settings: provider)
    monkeypatch.setattr(events_session_module, "uuid4", lambda: FakeUuid(next(uuid_values)))
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(
            app,
            ["--events", "--no-project-init", "-p", "write"],
            input=ApprovalResponseCommand(
                approval_id="approval-approval0000",
                approved=False,
                reason="not now",
            ).model_dump_json()
            + "\n",
        )

    messages = decode_output(result.output)
    approval = next(message for message in messages if isinstance(message, ApprovalRequestEvent))
    tool_result = next(message for message in messages if isinstance(message, ToolResultEvent))

    assert result.exit_code == 0
    assert approval.approval_id == "approval-approval0000"
    assert approval.tool_name == "write_file"
    assert tool_result.is_error is True
    assert tool_result.result_summary == "not now"


def test_events_cli_one_shot_malformed_approval_input_emits_protocol_error(
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
                        "name": "write_file",
                        "arguments": {"path": "new.txt", "content": "hello"},
                    },
                },
                {"type": "done"},
            ],
            [{"type": "text_delta", "content": "denied"}, {"type": "done"}],
        ]
    )
    monkeypatch.setattr(cli_main, "_build_provider", lambda _settings: provider)
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(
            app,
            ["--events", "--no-project-init", "-p", "write"],
            input="{not json}\n",
        )

    messages = decode_output(result.output)
    error = next(message for message in messages if isinstance(message, ErrorEvent))
    tool_result = next(message for message in messages if isinstance(message, ToolResultEvent))

    assert result.exit_code == 0
    assert error.code == protocol_error
    assert "Malformed protocol JSON" in error.message
    assert tool_result.is_error is True
    assert tool_result.result_summary == "Invalid approval response"


def test_events_cli_long_lived_accepts_start_turn_command(tmp_path: Path) -> None:
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path):
        command = StartTurnCommand(
            turn_id="turn-long",
            prompt="hello",
            workspace_root=str(Path.cwd()),
        )
        result = runner.invoke(
            app,
            ["--events", "--no-project-init"],
            input=command.model_dump_json() + "\n",
            env={"CODEGOPHER_TEST_MOCK_RESPONSE": "long answer"},
        )

    messages = decode_output(result.output)

    assert result.exit_code == 0
    assert [type(message) for message in messages] == [
        SessionStartedEvent,
        TurnStartedEvent,
        TextDeltaEvent,
        TurnCompleteEvent,
    ]
    assert messages[1].turn_id == "turn-long"
    assert messages[2].content == "long answer"
    assert messages[3].final_text == "long answer"


def test_events_cli_long_lived_accepts_config_and_mcp_commands(tmp_path: Path) -> None:
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path):
        workspace_root = str(Path.cwd())
        commands = [
            GetEffectiveConfigCommand(workspace_root=workspace_root),
            SaveMcpServerCommand(
                workspace_root=workspace_root,
                server_name="playwright",
                server=McpServerPayload(
                    transport="stdio",
                    command="npx",
                    args=["@playwright/mcp@latest"],
                ),
            ),
            ListMcpServersCommand(workspace_root=workspace_root),
            SetMcpServerEnabledCommand(
                workspace_root=workspace_root,
                server_name="playwright",
                enabled=False,
            ),
            DeleteMcpServerCommand(
                workspace_root=workspace_root,
                server_name="playwright",
            ),
        ]
        result = runner.invoke(
            app,
            ["--events", "--no-project-init"],
            input="".join(command.model_dump_json() + "\n" for command in commands),
            env={"CODEGOPHER_TEST_MOCK_RESPONSE": "unused"},
        )

    messages = decode_output(result.output)

    assert result.exit_code == 0
    assert any(isinstance(message, ConfigSnapshotEvent) for message in messages)
    saved = [
        message for message in messages if isinstance(message, McpServerSavedEvent)
    ]
    listed = next(message for message in messages if isinstance(message, McpServersEvent))
    deleted = next(message for message in messages if isinstance(message, McpServerDeletedEvent))
    assert saved[0].server_name == "playwright"
    assert saved[0].server.command == "npx"
    assert listed.servers[0].name == "playwright"
    assert saved[1].server.enabled is False
    assert deleted.server_name == "playwright"


def test_events_cli_long_lived_supports_cancel_turn(
    monkeypatch,
    tmp_path: Path,
) -> None:
    provider = WaitingProvider()
    monkeypatch.setattr(cli_main, "_build_provider", lambda _settings: provider)
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path):
        workspace_root = str(Path.cwd())
        commands = [
            StartTurnCommand(
                turn_id="turn-cancel",
                prompt="wait",
                workspace_root=workspace_root,
            ),
            CancelTurnCommand(turn_id="turn-cancel"),
        ]
        result = runner.invoke(
            app,
            ["--events", "--no-project-init"],
            input="".join(command.model_dump_json() + "\n" for command in commands),
        )

    messages = decode_output(result.output)
    error = next(message for message in messages if isinstance(message, ErrorEvent))

    assert result.exit_code == 0
    assert error.code == turn_cancelled
    assert error.turn_id == "turn-cancel"


def test_events_cli_long_lived_supports_shutdown(tmp_path: Path) -> None:
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(
            app,
            ["--events", "--no-project-init"],
            input=ShutdownCommand().model_dump_json() + "\n",
            env={"CODEGOPHER_TEST_MOCK_RESPONSE": "unused"},
        )

    messages = decode_output(result.output)

    assert result.exit_code == 0
    assert [type(message) for message in messages] == [SessionStartedEvent]


class WaitingProvider:
    capabilities = ProviderCapabilities(streaming=True, tool_calls=True)

    async def stream(
        self,
        messages,
        tools,
        *,
        model: str,
        temperature: float,
        max_output_tokens: int,
    ):
        _ = (messages, tools, model, temperature, max_output_tokens)
        await asyncio.Event().wait()
        yield {"type": "done"}
