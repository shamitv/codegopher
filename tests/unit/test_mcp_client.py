from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from codegopher.config.schema import McpConfig, McpServerConfig, McpTransport, Settings
from codegopher.core.errors import ConfigurationError, ToolExecutionError
from codegopher.mcp import McpManager, McpTool
from codegopher.tools.base import ToolContext
from codegopher.tools.registry import ToolRegistry


class FakeAsyncContext:
    def __init__(self, value: Any, events: list[str], label: str) -> None:
        self.value = value
        self.events = events
        self.label = label

    async def __aenter__(self):
        self.events.append(f"enter:{self.label}")
        return self.value

    async def __aexit__(self, *_exc_info):
        self.events.append(f"exit:{self.label}")


class FakeSession:
    def __init__(
        self,
        *,
        tools: list[dict[str, Any]] | None = None,
        result: Any | None = None,
        initialize_error: Exception | None = None,
    ) -> None:
        self.tools = tools or []
        self.result = result or {"content": [{"type": "text", "text": "ok"}], "isError": False}
        self.initialize_error = initialize_error
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self.initialized = False

    async def initialize(self) -> None:
        if self.initialize_error:
            raise self.initialize_error
        self.initialized = True

    async def list_tools(self) -> dict[str, Any]:
        return {"tools": self.tools}

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        self.calls.append((name, arguments))
        return self.result


def make_settings(*, servers: dict[str, McpServerConfig]) -> Settings:
    return Settings(mcp=McpConfig(servers=servers))


@pytest.mark.asyncio
async def test_mcp_manager_starts_stdio_lists_tools_and_cleans_up(tmp_path: Path) -> None:
    events: list[str] = []
    captured: dict[str, Any] = {}
    session = FakeSession(
        tools=[
            {
                "name": "echo",
                "description": "Echo text",
                "inputSchema": {"type": "object", "properties": {"text": {"type": "string"}}},
            }
        ]
    )

    def stdio_client(server: Any) -> FakeAsyncContext:
        captured["stdio_server"] = server
        return FakeAsyncContext(("read", "write"), events, "stdio")

    def session_factory(read_stream: Any, write_stream: Any) -> FakeAsyncContext:
        captured["streams"] = (read_stream, write_stream)
        return FakeAsyncContext(session, events, "session")

    manager = McpManager(
        settings=make_settings(
            servers={
                "local": McpServerConfig(
                    transport=McpTransport.stdio,
                    command="python",
                    args=["server.py"],
                    env={"LOCAL_ONLY": "1"},
                    cwd="server",
                )
            }
        ),
        cwd=tmp_path,
        environ={"PATH": "/bin"},
        stdio_client_factory=stdio_client,
        session_factory=session_factory,
    )

    await manager.start()

    assert session.initialized is True
    assert captured["streams"] == ("read", "write")
    assert captured["stdio_server"].command == "python"
    assert captured["stdio_server"].args == ["server.py"]
    assert captured["stdio_server"].env == {"PATH": "/bin", "LOCAL_ONLY": "1"}
    assert captured["stdio_server"].cwd == tmp_path / "server"
    assert manager.tools[0].name == "mcp__local__echo"
    assert manager.tools[0].requires_approval is True

    await manager.aclose()

    assert events == ["enter:stdio", "enter:session", "exit:session", "exit:stdio"]


@pytest.mark.asyncio
async def test_mcp_manager_starts_sse_with_headers_env(tmp_path: Path) -> None:
    captured: dict[str, Any] = {}
    session = FakeSession()

    def sse_client(
        url: str,
        *,
        headers: dict[str, Any] | None = None,
        timeout: float,
        sse_read_timeout: float,
    ) -> FakeAsyncContext:
        captured["sse"] = {
            "url": url,
            "headers": headers,
            "timeout": timeout,
            "sse_read_timeout": sse_read_timeout,
        }
        return FakeAsyncContext(("read", "write"), [], "sse")

    manager = McpManager(
        settings=make_settings(
            servers={
                "remote": McpServerConfig(
                    transport=McpTransport.sse,
                    url="http://127.0.0.1:9000/sse",
                    headers={"X-Static": "static"},
                    headers_env={"Authorization": "MCP_TOKEN"},
                    timeout_seconds=2.0,
                    sse_read_timeout_seconds=9.0,
                )
            }
        ),
        cwd=tmp_path,
        environ={"MCP_TOKEN": "Bearer secret"},
        sse_client_factory=sse_client,
        session_factory=lambda _read, _write: FakeAsyncContext(session, [], "session"),
    )

    await manager.start()

    assert captured["sse"] == {
        "url": "http://127.0.0.1:9000/sse",
        "headers": {"X-Static": "static", "Authorization": "Bearer secret"},
        "timeout": 2.0,
        "sse_read_timeout": 9.0,
    }


@pytest.mark.asyncio
async def test_mcp_manager_missing_sse_header_env_fails_without_secret_values(
    tmp_path: Path,
) -> None:
    manager = McpManager(
        settings=make_settings(
            servers={
                "remote": McpServerConfig(
                    transport=McpTransport.sse,
                    url="http://127.0.0.1:9000/sse",
                    headers_env={"Authorization": "MCP_TOKEN"},
                )
            }
        ),
        cwd=tmp_path,
        environ={"OTHER_SECRET": "do-not-print"},
    )

    with pytest.raises(ConfigurationError) as exc_info:
        await manager.start()

    message = str(exc_info.value)
    assert "MCP_TOKEN" in message
    assert "Authorization" in message
    assert "do-not-print" not in message


@pytest.mark.asyncio
async def test_mcp_manager_closes_started_contexts_on_failure(tmp_path: Path) -> None:
    events: list[str] = []
    session = FakeSession(initialize_error=RuntimeError("boom"))
    manager = McpManager(
        settings=make_settings(
            servers={
                "local": McpServerConfig(
                    transport=McpTransport.stdio,
                    command="python",
                )
            }
        ),
        cwd=tmp_path,
        environ={},
        stdio_client_factory=lambda _server: FakeAsyncContext(("read", "write"), events, "stdio"),
        session_factory=lambda _read, _write: FakeAsyncContext(session, events, "session"),
    )

    with pytest.raises(ConfigurationError, match=r"local \(stdio\)"):
        await manager.start()

    assert events == ["enter:stdio", "enter:session", "exit:session", "exit:stdio"]


@pytest.mark.asyncio
async def test_mcp_tool_executes_and_serializes_text_result(tmp_path: Path) -> None:
    session = FakeSession(result={"content": [{"type": "text", "text": "hello"}], "isError": False})
    tool = McpTool(
        server_name="playwright",
        original_name="browser_click",
        description="Click",
        parameters={"type": "object", "properties": {}},
        session=session,
    )

    result = await tool.execute(
        {"selector": "#submit", "_tool_call_id": "call-1"},
        ToolContext(cwd=tmp_path),
    )

    assert result.content == "hello"
    assert result.tool_call_id == "call-1"
    assert result.is_error is False
    assert session.calls == [("browser_click", {"selector": "#submit"})]


@pytest.mark.asyncio
async def test_mcp_tool_serializes_structured_result_deterministically(tmp_path: Path) -> None:
    session = FakeSession(
        result={
            "content": [{"type": "text", "text": "done"}],
            "structuredContent": {"z": 1, "a": [2]},
            "isError": True,
        }
    )
    tool = McpTool(
        server_name="remote",
        original_name="inspect",
        description="Inspect",
        parameters={"type": "object", "properties": {}},
        session=session,
    )

    result = await tool.execute({"_tool_call_id": "call-1"}, ToolContext(cwd=tmp_path))

    assert result.content == (
        '{"content": [{"text": "done", "type": "text"}], '
        '"structuredContent": {"a": [2], "z": 1}}'
    )
    assert result.is_error is True


def test_mcp_registry_duplicate_protection() -> None:
    registry = ToolRegistry()
    first = McpTool(
        server_name="srv",
        original_name="tool!",
        description="First",
        parameters={"type": "object", "properties": {}},
        session=FakeSession(),
    )
    second = McpTool(
        server_name="srv",
        original_name="tool@",
        description="Second",
        parameters={"type": "object", "properties": {}},
        session=FakeSession(),
    )

    registry.register(first)

    with pytest.raises(ToolExecutionError, match="Duplicate tool"):
        registry.register(second)
