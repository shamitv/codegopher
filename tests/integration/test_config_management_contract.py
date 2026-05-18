from __future__ import annotations

from pathlib import Path

from codegopher.config.loader import load_settings
from codegopher.config.management import (
    delete_mcp_server,
    ensure_project_mcp_servers_table,
    load_project_settings_document,
    save_mcp_server,
    set_mcp_server_enabled,
    write_project_settings_document,
)
from codegopher.config.schema import McpServerConfig


def test_project_settings_writer_contract_is_visible_to_settings_loader(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    home = tmp_path / "home"
    project.mkdir()
    home.mkdir()
    document = load_project_settings_document(project)
    servers = ensure_project_mcp_servers_table(document)
    servers["playwright"] = {
        "transport": "stdio",
        "command": "npx",
        "args": ["@playwright/mcp@latest"],
    }

    write_project_settings_document(project, document)
    settings = load_settings(cwd=project, home=home, environ={})

    assert settings.mcp.servers["playwright"].command == "npx"
    assert settings.mcp.servers["playwright"].args == ["@playwright/mcp@latest"]


def test_save_mcp_server_contract_round_trips_through_settings_loader(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    home = tmp_path / "home"
    project.mkdir()
    home.mkdir()

    save_mcp_server(
        project,
        "remote_docs",
        McpServerConfig(
            transport="sse",
            url="https://example.test/sse",
            headers_env={"Authorization": "MCP_AUTH"},
        ),
    )

    settings = load_settings(cwd=project, home=home, environ={})

    assert settings.mcp.servers["remote_docs"].transport.value == "sse"
    assert settings.mcp.servers["remote_docs"].url == "https://example.test/sse"
    assert settings.mcp.servers["remote_docs"].headers_env == {"Authorization": "MCP_AUTH"}


def test_mcp_server_enable_disable_delete_contract_round_trips(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    home = tmp_path / "home"
    project.mkdir()
    home.mkdir()
    save_mcp_server(
        project,
        "playwright",
        McpServerConfig(transport="stdio", command="npx"),
    )

    set_mcp_server_enabled(project, "playwright", False)
    disabled = load_settings(cwd=project, home=home, environ={})
    set_mcp_server_enabled(project, "playwright", True)
    enabled = load_settings(cwd=project, home=home, environ={})
    delete_mcp_server(project, "playwright")
    deleted = load_settings(cwd=project, home=home, environ={})

    assert disabled.mcp.servers["playwright"].enabled is False
    assert enabled.mcp.servers["playwright"].enabled is True
    assert "playwright" not in deleted.mcp.servers
