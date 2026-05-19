"""Settings loader."""

from __future__ import annotations

import copy
import os
import tomllib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from pydantic import ValidationError

from codegopher.config.schema import Settings
from codegopher.core.errors import ConfigurationError


@dataclass(frozen=True)
class CliOverrides:
    model: str | None = None
    provider: str | None = None
    base_url: str | None = None
    api_family: str | None = None
    approval_mode: str | None = None
    max_iterations: int | None = None
    debug: bool | None = None


@dataclass(frozen=True)
class SettingsMetadata:
    cwd: Path
    home: Path
    source_labels: tuple[str, ...]
    home_config_path: Path
    project_config_path: Path
    home_config: dict[str, Any]
    project_config: dict[str, Any]


@dataclass(frozen=True)
class LoadedSettings:
    settings: Settings
    metadata: SettingsMetadata


def _merge(base: dict[str, Any], update: dict[str, Any]) -> dict[str, Any]:
    merged = copy.deepcopy(base)
    for key, value in update.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _load_toml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        with path.open("rb") as handle:
            value = tomllib.load(handle)
    except tomllib.TOMLDecodeError as exc:
        raise ConfigurationError(f"Invalid TOML in {path}: {exc}") from exc
    return value


def _validate(data: dict[str, Any], *, source: str) -> Settings:
    try:
        return Settings.model_validate(data)
    except ValidationError as exc:
        raise ConfigurationError(f"Invalid settings from {source}: {exc}") from exc


def _ensure_provider_entry(data: dict[str, Any]) -> dict[str, Any]:
    model = data.setdefault("model", {})
    provider = str(model.get("provider", "openai"))
    name = str(model.get("name", "gpt-4o"))
    providers = data.setdefault("providers", {})
    entries = providers.setdefault(provider, [])
    if not entries:
        entries.append({"id": name, "name": name})
    return cast("dict[str, Any]", entries[0])


def _env_overrides(environ: Mapping[str, str]) -> dict[str, Any]:
    data: dict[str, Any] = {}
    if model := environ.get("CODEGOPHER_MODEL"):
        data = _merge(data, {"model": {"name": model}})
    if provider := environ.get("CODEGOPHER_PROVIDER"):
        data = _merge(data, {"model": {"provider": provider}})
    if approval_mode := environ.get("CODEGOPHER_APPROVAL_MODE"):
        data["approval_mode"] = approval_mode
    if debug := environ.get("CODEGOPHER_DEBUG"):
        data["debug"] = debug.lower() in {"1", "true", "yes", "on"}
    if base_url := environ.get("CODEGOPHER_BASE_URL"):
        _ensure_provider_entry(data)["base_url"] = base_url
    if api_key_env := environ.get("CODEGOPHER_API_KEY_ENV"):
        _ensure_provider_entry(data)["api_key_env"] = api_key_env
    if api_family := environ.get("CODEGOPHER_API_FAMILY"):
        _ensure_provider_entry(data)["api_family"] = api_family
    return data


def _cli_overrides(overrides: CliOverrides | None) -> dict[str, Any]:
    if overrides is None:
        return {}
    data: dict[str, Any] = {}
    if overrides.model:
        data = _merge(data, {"model": {"name": overrides.model}})
    if overrides.provider:
        data = _merge(data, {"model": {"provider": overrides.provider}})
    if overrides.approval_mode:
        data["approval_mode"] = overrides.approval_mode
    if overrides.max_iterations is not None:
        data = _merge(data, {"agent": {"max_iterations": overrides.max_iterations}})
    if overrides.debug is not None:
        data["debug"] = overrides.debug
    if overrides.base_url:
        _ensure_provider_entry(data)["base_url"] = overrides.base_url
    if overrides.api_family:
        _ensure_provider_entry(data)["api_family"] = overrides.api_family
    return data


def _apply_non_cli_env_overrides(data: dict[str, Any], environ: Mapping[str, str]) -> None:
    """Re-apply env-only provider fields that have no CLI flag equivalent."""
    if api_key_env := environ.get("CODEGOPHER_API_KEY_ENV"):
        _ensure_provider_entry(data)["api_key_env"] = api_key_env


def load_settings(
    *,
    cwd: Path | None = None,
    home: Path | None = None,
    environ: Mapping[str, str] | None = None,
    cli_overrides: CliOverrides | None = None,
) -> Settings:
    return load_settings_with_metadata(
        cwd=cwd,
        home=home,
        environ=environ,
        cli_overrides=cli_overrides,
    ).settings


def load_settings_with_metadata(
    *,
    cwd: Path | None = None,
    home: Path | None = None,
    environ: Mapping[str, str] | None = None,
    cli_overrides: CliOverrides | None = None,
) -> LoadedSettings:
    project_root = cwd or Path.cwd()
    home_root = home or Path.home()
    env = environ or os.environ
    home_config_path = home_root / ".codegopher" / "settings.toml"
    project_config_path = project_root / ".codegopher" / "settings.toml"
    home_config = _load_toml(home_config_path)
    project_config = _load_toml(project_config_path)
    env_config = _env_overrides(env)
    cli_config = _cli_overrides(cli_overrides)

    data: dict[str, Any] = {}
    data = _merge(data, home_config)
    data = _merge(data, project_config)
    data = _merge(data, env_config)
    data = _merge(data, cli_config)
    _apply_non_cli_env_overrides(data, env)

    sources: list[str] = []
    if home_config or project_config:
        sources.append("configuration files")
    if env_config:
        sources.append("environment variables")
    if cli_config:
        sources.append("CLI overrides")

    source_labels = ["defaults"]
    if home_config:
        source_labels.append("user")
    if project_config:
        source_labels.append("project")
    if env_config:
        source_labels.append("environment")
    if cli_config:
        source_labels.append("cli")

    return LoadedSettings(
        settings=_validate(data, source=", ".join(sources) or "defaults"),
        metadata=SettingsMetadata(
            cwd=project_root,
            home=home_root,
            source_labels=tuple(source_labels),
            home_config_path=home_config_path,
            project_config_path=project_config_path,
            home_config=copy.deepcopy(home_config),
            project_config=copy.deepcopy(project_config),
        ),
    )
