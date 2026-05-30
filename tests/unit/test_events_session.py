from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import pytest

from codegopher.config.loader import load_settings
from codegopher.config.schema import ApprovalMode, ModelConfig, Settings
from codegopher.core.errors import AgentLoopError, ConfigurationError, ProviderError
from codegopher.core.types import Message, ToolSchema
from codegopher.events.protocol import (
    ApprovalRequestEvent,
    ConfigSnapshotEvent,
    ErrorEvent,
    McpServerPayload,
    McpServerSavedEvent,
    McpServersEvent,
    ProviderRecoveryEvent,
    SessionStartedEvent,
    TaskContractCompletedEvent,
    TaskContractGateFailedEvent,
    TaskContractStartedEvent,
    ToolResultEvent,
    TurnCompleteEvent,
    TurnStartedEvent,
)
from codegopher.events.session import (
    EventsSession,
    agent_loop_error,
    bad_approval_state,
    configuration_error,
    provider_error,
    turn_cancelled,
)
from codegopher.providers.base import ProviderCapabilities
from codegopher.providers.mock import MockProvider
from codegopher.tools.base import ToolContext, ToolResult
from codegopher.tools.registry import ToolRegistry

VALID_CHAINED_REPORT = """# Chained Vulnerabilities Review

## Candidate Chain Ledger

```json
{"candidate_chains":[{"status":"complete","family":"auth","source":[{"path":"app.py","symbol":"route","line":1}],"hop":[{"path":"app.py","symbol":"check","line":2}],"sink":[{"path":"app.py","symbol":"sink","line":3}],"safe_controls":[{"path":"app.py","symbol":"guard","line":4,"classification":"nearby_only"}],"confidence":"High","missing_evidence":[]}]}
```
"""


def make_settings(approval_mode: ApprovalMode = ApprovalMode.yolo) -> Settings:
    return Settings(
        model=ModelConfig(provider="openai", name="test-model"),
        approval_mode=approval_mode,
    )


def make_registry(*tools: FakeTool) -> ToolRegistry:
    registry = ToolRegistry()
    for tool in tools:
        registry.register(tool)
    return registry


async def wait_for_event(events: list[Any], event_type: type[Any]) -> Any:
    for _ in range(50):
        for event in events:
            if isinstance(event, event_type):
                return event
        await asyncio.sleep(0.01)
    raise AssertionError(f"Timed out waiting for {event_type.__name__}")


@pytest.mark.asyncio
async def test_events_session_start_emits_session_started_and_registers_mcp_tool(
    tmp_path: Path,
) -> None:
    events: list[str] = []

    class FakeMcpManager:
        async def start(self):
            events.append("start")
            return self

        def register_tools(self, registry: ToolRegistry) -> None:
            events.append("register")
            registry.register(FakeTool(name="mcp__local__echo"))

        async def aclose(self) -> None:
            events.append("close")

    session = EventsSession(
        settings=make_settings(),
        cwd=tmp_path,
        provider_factory=lambda _settings: MockProvider([[{"type": "done"}]]),
        mcp_manager_factory=lambda _settings, _cwd: FakeMcpManager(),
        session_id="session-1",
    )

    await session.start()
    assert isinstance(session.events[0], SessionStartedEvent)
    assert session.events[0].session_id == "session-1"
    assert "mcp__local__echo" in [tool.name for tool in session.registry.list()]

    await session.aclose()
    assert events == ["start", "register", "close"]


@pytest.mark.asyncio
async def test_events_session_emits_turn_protocol_events_in_order(
    tmp_path: Path,
) -> None:
    (tmp_path / "README.md").write_text("project notes", encoding="utf-8")
    provider = MockProvider(
        [
            [
                {"type": "reasoning_delta", "content": "need file"},
                {"type": "text_delta", "content": "checking"},
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
            [{"type": "text_delta", "content": "done"}, {"type": "done"}],
        ]
    )
    session = EventsSession(
        settings=make_settings(),
        cwd=tmp_path,
        provider_factory=lambda _settings: provider,
    )

    result = await session.run_turn("inspect", turn_id="turn-1")

    assert result.final_text == "done"
    assert result.tool_count == 1
    assert result.approval_count == 0
    assert [event.type for event in session.events] == [
        "session_started",
        "turn_started",
        "reasoning_delta",
        "text_delta",
        "tool_call",
        "tool_result",
        "text_delta",
        "turn_complete",
    ]
    assert session.events[4].arguments_summary == '{"path": "README.md"}'
    assert session.events[5].result_summary == "project notes"
    assert isinstance(session.events[-1], TurnCompleteEvent)
    assert session.events[-1].final_text == "done"


@pytest.mark.asyncio
async def test_events_session_emits_provider_recovery_event_for_malformed_tool_json(
    tmp_path: Path,
) -> None:
    provider = MockProvider(
        [
            [
                {
                    "type": "error",
                    "code": "malformed_tool_arguments",
                    "message": "Malformed JSON in tool arguments: Unterminated string",
                    "tool_name": "read_file",
                    "tool_call_id": "call-read",
                    "tool_call_parse_error": {
                        "position": 12,
                        "payload_length": 40,
                    },
                }
            ],
            [{"type": "text_delta", "content": "recovered"}, {"type": "done"}],
        ]
    )
    session = EventsSession(
        settings=make_settings(),
        cwd=tmp_path,
        provider_factory=lambda _settings: provider,
    )

    result = await session.run_turn("inspect", turn_id="turn-1")

    recovery = next(
        event for event in session.events if isinstance(event, ProviderRecoveryEvent)
    )
    assert result.final_text == "recovered"
    assert recovery.tool_name == "read_file"
    assert recovery.tool_call_id == "call-read"
    assert recovery.recovery_attempt == 1
    assert recovery.will_retry is True
    assert recovery.parse_error["payload_length"] == 40


@pytest.mark.asyncio
async def test_events_session_preserves_prior_read_and_directory_state_across_turns(
    tmp_path: Path,
) -> None:
    (tmp_path / "existing.txt").write_text("old", encoding="utf-8")
    provider = MockProvider(
        [
            [
                {
                    "type": "tool_call",
                    "tool_call": {
                        "id": "call-1",
                        "name": "read_file",
                        "arguments": {"path": "existing.txt"},
                    },
                },
                {
                    "type": "tool_call",
                    "tool_call": {
                        "id": "call-2",
                        "name": "list_dir",
                        "arguments": {"path": "."},
                    },
                },
                {"type": "done"},
            ],
            [{"type": "text_delta", "content": "ready"}, {"type": "done"}],
            [
                {
                    "type": "tool_call",
                    "tool_call": {
                        "id": "call-3",
                        "name": "write_file",
                        "arguments": {"path": "existing.txt", "content": "new"},
                    },
                },
                {
                    "type": "tool_call",
                    "tool_call": {
                        "id": "call-4",
                        "name": "write_file",
                        "arguments": {"path": "new.txt", "content": "hello"},
                    },
                },
                {"type": "done"},
            ],
            [{"type": "text_delta", "content": "updated"}, {"type": "done"}],
        ]
    )
    session = EventsSession(
        settings=make_settings(),
        cwd=tmp_path,
        provider_factory=lambda _settings: provider,
    )

    await session.run_turn("prepare")
    second = await session.run_turn("write")

    assert second.final_text == "updated"
    tool_results = [
        event for event in session.events if isinstance(event, ToolResultEvent)
    ]
    assert [event.is_error for event in tool_results] == [False, False, False, False]
    assert (tmp_path / "existing.txt").read_text(encoding="utf-8") == "new"
    assert (tmp_path / "new.txt").read_text(encoding="utf-8") == "hello"


@pytest.mark.asyncio
async def test_events_session_bridges_approval_responses(tmp_path: Path) -> None:
    tool = FakeTool(name="write_file", requires_approval=True)
    provider = MockProvider(
        [
            [
                {
                    "type": "tool_call",
                    "tool_call": {
                        "id": "call-1",
                        "name": "write_file",
                        "arguments": {
                            "path": "new.txt",
                            "api_token": "secret-token",
                        },
                    },
                },
                {"type": "done"},
            ],
            [{"type": "text_delta", "content": "approved"}, {"type": "done"}],
        ]
    )
    session = EventsSession(
        settings=make_settings(ApprovalMode.review),
        cwd=tmp_path,
        provider_factory=lambda _settings: provider,
        registry_factory=lambda: make_registry(tool),
    )

    turn_task = asyncio.create_task(session.run_turn("write", turn_id="turn-1"))
    approval_event = await wait_for_event(session.events, ApprovalRequestEvent)

    assert approval_event.tool_name == "write_file"
    assert approval_event.raw_arguments == {
        "path": "new.txt",
        "api_token": "[redacted]",
    }
    assert "secret-token" not in approval_event.arguments_summary

    accepted = await session.submit_approval(
        approval_event.approval_id,
        approved=True,
    )
    result = await turn_task

    assert accepted is True
    assert result.final_text == "approved"
    assert result.approval_count == 1
    assert tool.executed is True


@pytest.mark.asyncio
async def test_events_session_bad_approval_state_emits_structured_error(
    tmp_path: Path,
) -> None:
    session = EventsSession(
        settings=make_settings(),
        cwd=tmp_path,
        provider_factory=lambda _settings: MockProvider([[{"type": "done"}]]),
    )

    accepted = await session.submit_approval("missing", approved=True)

    assert accepted is False
    assert isinstance(session.events[-1], ErrorEvent)
    assert session.events[-1].code == bad_approval_state


@pytest.mark.asyncio
async def test_events_session_maps_provider_errors_once(tmp_path: Path) -> None:
    session = EventsSession(
        settings=make_settings(),
        cwd=tmp_path,
        provider_factory=lambda _settings: MockProvider(
            [[{"type": "error", "message": "provider failed"}]]
        ),
    )

    with pytest.raises(ProviderError, match="provider failed"):
        await session.run_turn("fail", turn_id="turn-1")

    errors = [event for event in session.events if isinstance(event, ErrorEvent)]
    assert [(event.code, event.message) for event in errors] == [
        (provider_error, "provider failed")
    ]


@pytest.mark.asyncio
async def test_events_session_maps_agent_loop_errors(tmp_path: Path) -> None:
    provider = MockProvider(
        [
            [
                {
                    "type": "tool_call",
                    "tool_call": {
                        "id": "call-1",
                        "name": "read_file",
                        "arguments": {"path": "missing.txt"},
                    },
                },
                {"type": "done"},
            ]
        ]
    )
    session = EventsSession(
        settings=make_settings(),
        cwd=tmp_path,
        provider_factory=lambda _settings: provider,
        max_iterations=1,
    )

    with pytest.raises(AgentLoopError, match="max iterations"):
        await session.run_turn("read", turn_id="turn-1")

    errors = [event for event in session.events if isinstance(event, ErrorEvent)]
    assert errors[-1].code == agent_loop_error
    assert "max iterations" in errors[-1].message


@pytest.mark.asyncio
async def test_events_session_emits_task_contract_lifecycle_events(
    tmp_path: Path,
) -> None:
    provider = MockProvider(
        [
            [{"type": "text_delta", "content": "not done"}, {"type": "done"}],
            [
                {
                    "type": "tool_call",
                    "tool_call": {
                        "id": "call-report",
                        "name": "write_chained_vulnerability_report",
                        "arguments": {"content": VALID_CHAINED_REPORT},
                    },
                },
                {"type": "done"},
            ],
            [{"type": "text_delta", "content": "done"}, {"type": "done"}],
        ]
    )
    session = EventsSession(
        settings=make_settings(),
        cwd=tmp_path,
        provider_factory=lambda _settings: provider,
    )

    result = await session.run_turn(
        "use @skill:chained-vulnerability-static-audit",
        turn_id="turn-contract",
    )

    assert result.final_text == "done"
    assert any(isinstance(event, TaskContractStartedEvent) for event in session.events)
    assert any(isinstance(event, TaskContractGateFailedEvent) for event in session.events)
    completed = [
        event
        for event in session.events
        if isinstance(event, TaskContractCompletedEvent)
    ]
    assert completed[-1].status == "completed"


@pytest.mark.asyncio
async def test_events_session_config_helpers_emit_redacted_mcp_events(
    tmp_path: Path,
) -> None:
    session = EventsSession(
        settings=make_settings(),
        cwd=tmp_path,
        provider_factory=lambda _settings: MockProvider([[{"type": "done"}]]),
        home=tmp_path / "home",
        environ={},
    )

    config = await session.emit_effective_config()
    saved = await session.save_mcp_server(
        "remote_docs",
        McpServerPayload(
            transport="sse",
            url="https://example.test/sse",
            headers={"Authorization": "Bearer real-secret"},
            headers_env={"X-Token": "MCP_TOKEN"},
        ),
    )
    servers = await session.emit_mcp_servers()
    disabled = await session.set_mcp_server_enabled("remote_docs", False)
    deleted = await session.delete_mcp_server("remote_docs")

    assert isinstance(config, ConfigSnapshotEvent)
    assert config.provider == "openai"
    assert config.replay_reasoning_content is False
    assert config.config_sources == ["defaults"]
    assert isinstance(saved, McpServerSavedEvent)
    assert saved.server.headers == {"Authorization": "[redacted]"}
    assert saved.server.headers_env == {"X-Token": "[redacted]"}
    assert "real-secret" not in repr(saved)
    assert isinstance(servers, McpServersEvent)
    assert servers.servers[0].name == "remote_docs"
    assert disabled.server.enabled is False
    assert deleted.server_name == "remote_docs"
    settings = load_settings(cwd=tmp_path, home=tmp_path / "home", environ={})
    assert "remote_docs" not in settings.mcp.servers


@pytest.mark.asyncio
async def test_events_session_config_failures_emit_structured_errors(
    tmp_path: Path,
) -> None:
    config_dir = tmp_path / ".codegopher"
    config_dir.mkdir()
    (config_dir / "settings.toml").write_text("[model\n", encoding="utf-8")
    session = EventsSession(
        settings=make_settings(),
        cwd=tmp_path,
        provider_factory=lambda _settings: MockProvider([[{"type": "done"}]]),
        home=tmp_path / "home",
        environ={},
    )

    with pytest.raises(ConfigurationError, match="Invalid TOML"):
        await session.emit_effective_config()

    assert isinstance(session.events[-1], ErrorEvent)
    assert session.events[-1].code == configuration_error


@pytest.mark.asyncio
async def test_events_session_reusable_after_cancellation(tmp_path: Path) -> None:
    provider = WaitingProvider()
    session = EventsSession(
        settings=make_settings(),
        cwd=tmp_path,
        provider_factory=lambda _settings: provider,
    )

    turn_task = asyncio.create_task(session.run_turn("wait", turn_id="turn-1"))
    await asyncio.wait_for(provider.started.wait(), timeout=1)

    cancelled = await session.cancel_turn("turn-1")
    first = await turn_task
    second = await session.run_turn("again", turn_id="turn-2")

    assert cancelled is True
    assert first.cancelled is True
    assert second.final_text == "after cancel"
    errors = [event for event in session.events if isinstance(event, ErrorEvent)]
    assert errors[-1].code == turn_cancelled
    assert any(
        isinstance(event, TurnStartedEvent) and event.turn_id == "turn-2"
        for event in session.events
    )


class FakeTool:
    description = "Fake test tool"
    parameters: dict[str, Any] = {"type": "object", "properties": {}}

    def __init__(self, *, name: str, requires_approval: bool = True) -> None:
        self.name = name
        self.requires_approval = requires_approval
        self.executed = False

    async def execute(self, arguments: dict[str, Any], context: ToolContext) -> ToolResult:
        self.executed = True
        return ToolResult(
            tool_call_id=str(arguments.get("_tool_call_id", "")),
            content="ok",
        )


class WaitingProvider:
    capabilities = ProviderCapabilities(streaming=True, tool_calls=True)

    def __init__(self) -> None:
        self.started = asyncio.Event()
        self.calls: list[list[Message]] = []

    async def stream(
        self,
        messages: list[Message],
        tools: list[ToolSchema],
        *,
        model: str,
        temperature: float,
        max_output_tokens: int,
    ):
        self.calls.append(messages)
        if len(self.calls) == 1:
            self.started.set()
            await asyncio.Event().wait()
        yield {"type": "text_delta", "content": "after cancel"}
        yield {"type": "done"}
