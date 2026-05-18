"""MCP client lifecycle and tool wrappers."""

from __future__ import annotations

import asyncio
import re
from collections.abc import Mapping
from contextlib import AbstractAsyncContextManager, AsyncExitStack
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from codegopher.config.schema import McpServerConfig, McpTransport, Settings
from codegopher.core.errors import ConfigurationError
from codegopher.tools.base import ToolContext, ToolResult
from codegopher.tools.registry import ToolRegistry
from codegopher.utils.json import dumps_json


class StdioClientFactory(Protocol):
    def __call__(self, server: Any) -> AbstractAsyncContextManager[tuple[Any, Any]]:
        ...


class SseClientFactory(Protocol):
    def __call__(
        self,
        url: str,
        *,
        headers: dict[str, Any] | None = None,
        timeout: float,
        sse_read_timeout: float,
    ) -> AbstractAsyncContextManager[tuple[Any, Any]]:
        ...


class SessionFactory(Protocol):
    def __call__(self, read_stream: Any, write_stream: Any) -> AbstractAsyncContextManager[Any]:
        ...


def _get(value: Any, key: str, default: Any = None) -> Any:
    if isinstance(value, dict):
        return value.get(key, default)
    return getattr(value, key, default)


def _jsonable(value: Any) -> Any:
    if isinstance(value, str | int | float | bool) or value is None:
        return value
    if isinstance(value, list | tuple):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if hasattr(value, "model_dump"):
        return _jsonable(value.model_dump(mode="json", exclude_none=True))
    if hasattr(value, "to_dict"):
        return _jsonable(value.to_dict())
    return str(value)


def _safe_tool_part(value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_-]+", "_", value).strip("_")
    return safe or "tool"


def _serialize_mcp_result(result: Any) -> str:
    content = _get(result, "content", []) or []
    structured = _get(result, "structuredContent")
    if (
        structured is None
        and len(content) == 1
        and str(_get(content[0], "type", "")) == "text"
    ):
        return str(_get(content[0], "text", ""))

    payload: dict[str, Any] = {}
    if content:
        payload["content"] = [_jsonable(item) for item in content]
    if structured is not None:
        payload["structuredContent"] = _jsonable(structured)
    if not payload:
        return ""
    return dumps_json(payload)


@dataclass
class McpTool:
    server_name: str
    original_name: str
    description: str
    parameters: dict[str, Any]
    session: Any
    requires_approval: bool = True
    name: str = field(init=False)

    def __post_init__(self) -> None:
        self.name = f"mcp__{_safe_tool_part(self.server_name)}__{_safe_tool_part(self.original_name)}"

    async def execute(self, arguments: dict[str, Any], context: ToolContext) -> ToolResult:
        tool_call_id = str(arguments.get("_tool_call_id", self.name))
        call_arguments = {
            key: value for key, value in arguments.items() if key != "_tool_call_id"
        }
        try:
            result = await self.session.call_tool(self.original_name, call_arguments)
        except Exception as exc:
            return ToolResult(tool_call_id=tool_call_id, content=str(exc), is_error=True)
        return ToolResult(
            tool_call_id=tool_call_id,
            content=_serialize_mcp_result(result),
            is_error=bool(_get(result, "isError", False)),
        )


def _default_stdio_client(server: Any) -> AbstractAsyncContextManager[tuple[Any, Any]]:
    from mcp.client.stdio import stdio_client

    return stdio_client(server)


def _default_sse_client(
    url: str,
    *,
    headers: dict[str, Any] | None = None,
    timeout: float,
    sse_read_timeout: float,
) -> AbstractAsyncContextManager[tuple[Any, Any]]:
    from mcp.client.sse import sse_client

    return sse_client(
        url,
        headers=headers,
        timeout=timeout,
        sse_read_timeout=sse_read_timeout,
    )


def _default_session_factory(
    read_stream: Any,
    write_stream: Any,
) -> AbstractAsyncContextManager[Any]:
    from mcp import ClientSession

    return ClientSession(read_stream, write_stream)


def _stdio_parameters(config: McpServerConfig, cwd: Path, environ: Mapping[str, str]) -> Any:
    from mcp import StdioServerParameters

    server_cwd: str | Path | None = config.cwd
    if server_cwd and not Path(server_cwd).is_absolute():
        server_cwd = cwd / server_cwd
    return StdioServerParameters(
        command=config.command or "",
        args=config.args,
        env={**environ, **config.env},
        cwd=server_cwd,
    )


def _resolve_sse_headers(
    *,
    server_name: str,
    config: McpServerConfig,
    environ: Mapping[str, str],
) -> dict[str, Any]:
    headers: dict[str, Any] = dict(config.headers)
    for header_name, env_name in config.headers_env.items():
        value = environ.get(env_name)
        if value is None:
            raise ConfigurationError(
                f"MCP server {server_name} SSE header {header_name} references "
                f"missing environment variable {env_name}"
            )
        headers[header_name] = value
    return headers


class McpManager:
    """Owns MCP sessions and exports discovered tools into CodeGopher."""

    def __init__(
        self,
        *,
        settings: Settings,
        cwd: Path,
        environ: Mapping[str, str],
        stdio_client_factory: StdioClientFactory = _default_stdio_client,
        sse_client_factory: SseClientFactory = _default_sse_client,
        session_factory: SessionFactory = _default_session_factory,
    ) -> None:
        self.settings = settings
        self.cwd = cwd
        self.environ = environ
        self.stdio_client_factory = stdio_client_factory
        self.sse_client_factory = sse_client_factory
        self.session_factory = session_factory
        self._exit_stack = AsyncExitStack()
        self._tools: list[McpTool] = []
        self._started = False

    @property
    def tools(self) -> list[McpTool]:
        return list(self._tools)

    async def start(self) -> McpManager:
        if self._started or not self.settings.mcp.enabled:
            self._started = True
            return self
        try:
            for server_name, config in self.settings.mcp.servers.items():
                if config.enabled:
                    await self._connect_server(server_name, config)
        except Exception:
            await self.aclose()
            raise
        self._started = True
        return self

    async def aclose(self) -> None:
        await self._exit_stack.aclose()
        self._tools.clear()
        self._started = False

    async def __aenter__(self) -> McpManager:
        return await self.start()

    async def __aexit__(self, *_exc_info: object) -> None:
        await self.aclose()

    def register_tools(self, registry: ToolRegistry) -> None:
        for tool in self._tools:
            registry.register(tool)

    async def _connect_server(self, server_name: str, config: McpServerConfig) -> None:
        try:
            if config.transport is McpTransport.stdio:
                streams = await self._exit_stack.enter_async_context(
                    self.stdio_client_factory(
                        _stdio_parameters(config, self.cwd, self.environ)
                    )
                )
                startup_timeout = config.startup_timeout_seconds
            else:
                streams = await self._exit_stack.enter_async_context(
                    self.sse_client_factory(
                        config.url or "",
                        headers=_resolve_sse_headers(
                            server_name=server_name,
                            config=config,
                            environ=self.environ,
                        ),
                        timeout=config.timeout_seconds,
                        sse_read_timeout=config.sse_read_timeout_seconds,
                    )
                )
                startup_timeout = config.timeout_seconds
            session = await self._exit_stack.enter_async_context(
                self.session_factory(streams[0], streams[1])
            )
            await asyncio.wait_for(session.initialize(), timeout=startup_timeout)
            tool_result = await asyncio.wait_for(
                session.list_tools(),
                timeout=startup_timeout,
            )
        except ConfigurationError:
            raise
        except Exception as exc:
            raise ConfigurationError(f"MCP server {server_name} failed to initialize: {exc}") from exc

        for raw_tool in _get(tool_result, "tools", []) or []:
            self._tools.append(
                McpTool(
                    server_name=server_name,
                    original_name=str(_get(raw_tool, "name", "")),
                    description=str(_get(raw_tool, "description", "") or ""),
                    parameters=dict(
                        _get(raw_tool, "inputSchema", {"type": "object", "properties": {}})
                    ),
                    session=session,
                )
            )
