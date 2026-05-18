from __future__ import annotations

from pathlib import Path

from codegopher.config.management import (
    ensure_project_mcp_servers_table,
    load_project_settings_document,
    project_settings_path,
    write_project_settings_document,
)


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
