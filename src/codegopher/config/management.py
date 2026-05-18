"""Project-local configuration management helpers for IDE integrations."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

import tomlkit
from tomlkit.items import Table
from tomlkit.toml_document import TOMLDocument

from codegopher.core.errors import ConfigurationError


def project_settings_path(cwd: Path) -> Path:
    return cwd / ".codegopher" / "settings.toml"


def load_project_settings_document(cwd: Path) -> TOMLDocument:
    path = project_settings_path(cwd)
    if not path.exists():
        return tomlkit.document()
    try:
        return tomlkit.parse(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
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


__all__ = [
    "ensure_project_mcp_servers_table",
    "load_project_settings_document",
    "project_mcp_servers_table",
    "project_settings_path",
    "table_to_plain_dict",
    "write_project_settings_document",
]
