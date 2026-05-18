"""Configuration inspection helpers for IDE integrations."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from codegopher.config.loader import (
    CliOverrides,
    SettingsMetadata,
    load_settings_with_metadata,
)
from codegopher.config.schema import McpServerConfig
from codegopher.core.context_budget import selected_provider_entry
from codegopher.events.protocol import McpServerPayload, redact_protocol_value


@dataclass(frozen=True)
class EffectiveConfigSnapshot:
    workspace_root: str
    provider: str
    model: str
    provider_entry_id: str | None
    provider_entry_name: str | None
    api_family: str
    base_url: str | None
    config_sources: tuple[str, ...]


@dataclass(frozen=True)
class McpServerSnapshot:
    name: str
    source: str
    server: McpServerPayload


def inspect_effective_config(
    *,
    cwd: Path | None = None,
    home: Path | None = None,
    environ: Mapping[str, str] | None = None,
    cli_overrides: CliOverrides | None = None,
) -> EffectiveConfigSnapshot:
    loaded = load_settings_with_metadata(
        cwd=cwd,
        home=home,
        environ=environ,
        cli_overrides=cli_overrides,
    )
    settings = loaded.settings
    selected_entry = selected_provider_entry(settings)
    return EffectiveConfigSnapshot(
        workspace_root=str(loaded.metadata.cwd),
        provider=settings.model.provider,
        model=settings.model.name,
        provider_entry_id=selected_entry.id if selected_entry else None,
        provider_entry_name=selected_entry.name if selected_entry else None,
        api_family=(
            selected_entry.api_family.value
            if selected_entry
            else "chat_completions"
        ),
        base_url=selected_entry.base_url if selected_entry else None,
        config_sources=loaded.metadata.source_labels,
    )


def list_mcp_servers(
    *,
    cwd: Path | None = None,
    home: Path | None = None,
    environ: Mapping[str, str] | None = None,
    cli_overrides: CliOverrides | None = None,
) -> tuple[McpServerSnapshot, ...]:
    loaded = load_settings_with_metadata(
        cwd=cwd,
        home=home,
        environ=environ,
        cli_overrides=cli_overrides,
    )
    server_sources = _mcp_server_sources(loaded.metadata)
    return tuple(
        McpServerSnapshot(
            name=name,
            source=server_sources.get(name, "defaults"),
            server=_redacted_mcp_payload(server),
        )
        for name, server in sorted(loaded.settings.mcp.servers.items())
    )


def _mcp_server_sources(metadata: SettingsMetadata) -> dict[str, str]:
    sources: dict[str, str] = {}
    for name in _configured_mcp_server_names(metadata.home_config):
        sources[name] = "user"
    for name in _configured_mcp_server_names(metadata.project_config):
        sources[name] = "project"
    return sources


def _configured_mcp_server_names(data: Mapping[str, object]) -> set[str]:
    mcp = data.get("mcp")
    if not isinstance(mcp, dict):
        return set()
    servers = mcp.get("servers")
    if not isinstance(servers, dict):
        return set()
    return {str(name) for name in servers}


def _redacted_mcp_payload(server: McpServerConfig) -> McpServerPayload:
    raw_payload = server.model_dump(mode="json")
    redacted = redact_protocol_value(raw_payload)
    return McpServerPayload.model_validate(redacted)


__all__ = [
    "EffectiveConfigSnapshot",
    "McpServerSnapshot",
    "SettingsMetadata",
    "inspect_effective_config",
    "list_mcp_servers",
]
