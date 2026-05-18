"""Project-local configuration management helpers for IDE integrations."""

from __future__ import annotations

import tomllib
import re
from pathlib import Path
from typing import Any

import tomlkit
from pydantic import ValidationError
from tomlkit.exceptions import TOMLKitError
from tomlkit.items import Table
from tomlkit.toml_document import TOMLDocument

from codegopher.config.schema import McpServerConfig
from codegopher.core.errors import ConfigurationError

MCP_SERVER_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


def project_settings_path(cwd: Path) -> Path:
    return cwd / ".codegopher" / "settings.toml"


def load_project_settings_document(cwd: Path) -> TOMLDocument:
    path = project_settings_path(cwd)
    if not path.exists():
        return tomlkit.document()
    try:
        return tomlkit.parse(path.read_text(encoding="utf-8"))
    except (tomllib.TOMLDecodeError, TOMLKitError) as exc:
        raise ConfigurationError(f"Invalid TOML in {path}: {exc}") from exc


def write_project_settings_document(cwd: Path, document: TOMLDocument) -> Path:
    path = project_settings_path(cwd)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(tomlkit.dumps(document), encoding="utf-8")
    return path


def ensure_project_mcp_servers_table(document: TOMLDocument) -> Table:
    mcp = document.get("mcp")
    if mcp is None:
        mcp = tomlkit.table()
        document["mcp"] = mcp
    if not isinstance(mcp, Table):
        raise ConfigurationError("Project settings [mcp] must be a TOML table")
    servers = mcp.get("servers")
    if servers is None:
        servers = tomlkit.table()
        mcp["servers"] = servers
    if not isinstance(servers, Table):
        raise ConfigurationError("Project settings [mcp.servers] must be a TOML table")
    return servers


def project_mcp_servers_table(document: TOMLDocument) -> Table | None:
    mcp = document.get("mcp")
    if mcp is None:
        return None
    if not isinstance(mcp, Table):
        raise ConfigurationError("Project settings [mcp] must be a TOML table")
    servers = mcp.get("servers")
    if servers is None:
        return None
    if not isinstance(servers, Table):
        raise ConfigurationError("Project settings [mcp.servers] must be a TOML table")
    return servers


def table_to_plain_dict(table: Any) -> dict[str, Any]:
    value = table.unwrap() if hasattr(table, "unwrap") else table
    if not isinstance(value, dict):
        raise ConfigurationError("Expected TOML table")
    return dict(value)


def validate_mcp_server_name(server_name: str) -> None:
    if not MCP_SERVER_NAME_PATTERN.fullmatch(server_name):
        raise ConfigurationError(
            "MCP server names may contain only letters, numbers, '_' and '-'"
        )


def save_mcp_server(cwd: Path, server_name: str, server: McpServerConfig) -> Path:
    validate_mcp_server_name(server_name)
    try:
        normalized = McpServerConfig.model_validate(server.model_dump(mode="json"))
    except ValidationError as exc:
        raise ConfigurationError(f"Invalid MCP server {server_name}: {exc}") from exc
    document = load_project_settings_document(cwd)
    servers = ensure_project_mcp_servers_table(document)
    servers[server_name] = normalized.model_dump(mode="json", exclude_none=True)
    return write_project_settings_document(cwd, document)


def set_mcp_server_enabled(cwd: Path, server_name: str, enabled: bool) -> Path:
    validate_mcp_server_name(server_name)
    document = load_project_settings_document(cwd)
    servers = project_mcp_servers_table(document)
    if servers is None or server_name not in servers:
        raise ConfigurationError(f"MCP server not found: {server_name}")
    server_table = servers[server_name]
    if not isinstance(server_table, Table):
        raise ConfigurationError(f"Project MCP server {server_name} must be a TOML table")
    server_table["enabled"] = enabled
    return write_project_settings_document(cwd, document)


def delete_mcp_server(cwd: Path, server_name: str) -> Path:
    validate_mcp_server_name(server_name)
    document = load_project_settings_document(cwd)
    servers = project_mcp_servers_table(document)
    if servers is None or server_name not in servers:
        raise ConfigurationError(f"MCP server not found: {server_name}")
    del servers[server_name]
    return write_project_settings_document(cwd, document)


__all__ = [
    "ensure_project_mcp_servers_table",
    "delete_mcp_server",
    "load_project_settings_document",
    "project_mcp_servers_table",
    "project_settings_path",
    "save_mcp_server",
    "set_mcp_server_enabled",
    "table_to_plain_dict",
    "validate_mcp_server_name",
    "write_project_settings_document",
]
