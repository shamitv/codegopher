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
from codegopher.core.context_budget import selected_provider_entry


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


__all__ = [
    "EffectiveConfigSnapshot",
    "SettingsMetadata",
    "inspect_effective_config",
]
