from __future__ import annotations

from pathlib import Path

import pytest

from codegopher.config.loader import load_settings
from codegopher.config.management import (
    delete_mcp_server,
    ensure_project_mcp_servers_table,
    load_project_settings_document,
    project_settings_path,
    save_mcp_server,
    set_mcp_server_enabled,
    write_project_settings_document,
)
from codegopher.config.schema import McpServerConfig
from codegopher.core.errors import ConfigurationError


def test_project_settings_writer_creates_missing_file(tmp_path: Path) -> None:
    document = load_project_settings_document(tmp_path)
    document["approval_mode"] = "auto"

    path = write_project_settings_document(tmp_path, document)

    assert path == project_settings_path(tmp_path)
    assert path.read_text(encoding="utf-8") == 'approval_mode = "auto"\n'


def test_project_settings_writer_preserves_unrelated_settings_and_comments(
    tmp_path: Path,
) -> None:
    path = project_settings_path(tmp_path)
    path.parent.mkdir()
    path.write_text(
        """# keep this comment
approval_mode = "review"

[model]
name = "gpt-test"
""",
        encoding="utf-8",
    )
    document = load_project_settings_document(tmp_path)
    servers = ensure_project_mcp_servers_table(document)
    servers["playwright"] = {"transport": "stdio", "command": "npx"}

    write_project_settings_document(tmp_path, document)

    updated = path.read_text(encoding="utf-8")
    assert "# keep this comment" in updated
    assert 'approval_mode = "review"' in updated
    assert '[model]\nname = "gpt-test"' in updated
    assert "[mcp.servers.playwright]" in updated
    assert 'command = "npx"' in updated


def test_project_settings_writer_does_not_write_user_global_settings(
    tmp_path: Path,
) -> None:
    home = tmp_path / "home"
    project = tmp_path / "project"
    user_settings = home / ".codegopher/settings.toml"
    user_settings.parent.mkdir(parents=True)
    project.mkdir()
    user_settings.write_text('approval_mode = "review"\n', encoding="utf-8")
    document = load_project_settings_document(project)
    document["approval_mode"] = "auto"

    write_project_settings_document(project, document)

    assert user_settings.read_text(encoding="utf-8") == 'approval_mode = "review"\n'
    assert project_settings_path(project).exists()


def test_save_mcp_server_adds_stdio_server_and_loader_can_read_it(
    tmp_path: Path,
) -> None:
    save_mcp_server(
        tmp_path,
        "playwright",
        McpServerConfig(
            transport="stdio",
            command="npx",
            args=["@playwright/mcp@latest"],
        ),
    )

    settings = load_settings(cwd=tmp_path, home=tmp_path / "home", environ={})

    assert settings.mcp.servers["playwright"].command == "npx"
    assert settings.mcp.servers["playwright"].args == ["@playwright/mcp@latest"]


def test_save_mcp_server_edits_existing_server(tmp_path: Path) -> None:
    save_mcp_server(
        tmp_path,
        "playwright",
        McpServerConfig(transport="stdio", command="npx"),
    )
    save_mcp_server(
        tmp_path,
        "playwright",
        McpServerConfig(transport="stdio", command="node", args=["server.js"]),
    )

    settings = load_settings(cwd=tmp_path, home=tmp_path / "home", environ={})

    assert settings.mcp.servers["playwright"].command == "node"
    assert settings.mcp.servers["playwright"].args == ["server.js"]


def test_save_mcp_server_adds_sse_server(tmp_path: Path) -> None:
    save_mcp_server(
        tmp_path,
        "remote_docs",
        McpServerConfig(
            transport="sse",
            url="https://example.test/sse",
            headers_env={"Authorization": "MCP_AUTH"},
        ),
    )

    settings = load_settings(cwd=tmp_path, home=tmp_path / "home", environ={})

    assert settings.mcp.servers["remote_docs"].transport.value == "sse"
    assert settings.mcp.servers["remote_docs"].url == "https://example.test/sse"
    assert settings.mcp.servers["remote_docs"].headers_env == {"Authorization": "MCP_AUTH"}


def test_save_mcp_server_rejects_invalid_server_name(tmp_path: Path) -> None:
    with pytest.raises(ConfigurationError, match="MCP server names"):
        save_mcp_server(
            tmp_path,
            "bad.name",
            McpServerConfig(transport="stdio", command="npx"),
        )


def test_set_mcp_server_enabled_updates_existing_server(tmp_path: Path) -> None:
    save_mcp_server(
        tmp_path,
        "playwright",
        McpServerConfig(transport="stdio", command="npx"),
    )

    set_mcp_server_enabled(tmp_path, "playwright", False)
    disabled = load_settings(cwd=tmp_path, home=tmp_path / "home", environ={})
    set_mcp_server_enabled(tmp_path, "playwright", True)
    enabled = load_settings(cwd=tmp_path, home=tmp_path / "home", environ={})

    assert disabled.mcp.servers["playwright"].enabled is False
    assert enabled.mcp.servers["playwright"].enabled is True


def test_delete_mcp_server_removes_existing_server(tmp_path: Path) -> None:
    save_mcp_server(
        tmp_path,
        "playwright",
        McpServerConfig(transport="stdio", command="npx"),
    )

    delete_mcp_server(tmp_path, "playwright")
    settings = load_settings(cwd=tmp_path, home=tmp_path / "home", environ={})

    assert "playwright" not in settings.mcp.servers
