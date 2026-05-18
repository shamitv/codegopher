from __future__ import annotations

from pathlib import Path

from codegopher.config.loader import load_settings
from codegopher.config.management import (
    ensure_project_mcp_servers_table,
    load_project_settings_document,
    write_project_settings_document,
)


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
