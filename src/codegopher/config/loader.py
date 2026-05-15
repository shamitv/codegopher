"""Settings loader."""

from __future__ import annotations

import copy
import os
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from pydantic import ValidationError

from codegopher.core.errors import ConfigurationError
from codegopher.config.schema import Settings


@dataclass(frozen=True)
class CliOverrides:
    model: str | None = None
    provider: str | None = None
    base_url: str | None = None
    approval_mode: str | None = None
    debug: bool | None = None


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
    return entries[0]


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
    if overrides.debug is not None:
        data["debug"] = overrides.debug
    if overrides.base_url:
        _ensure_provider_entry(data)["base_url"] = overrides.base_url
    return data


def load_settings(
    *,
    cwd: Path | None = None,
    home: Path | None = None,
    environ: Mapping[str, str] | None = None,
    cli_overrides: CliOverrides | None = None,
) -> Settings:
    project_root = cwd or Path.cwd()
    home_root = home or Path.home()
    env = environ or os.environ
    data: dict[str, Any] = {}
    data = _merge(data, _load_toml(home_root / ".codegopher" / "settings.toml"))
    data = _merge(data, _load_toml(project_root / ".codegopher" / "settings.toml"))
    data = _merge(data, _env_overrides(env))
    data = _merge(data, _cli_overrides(cli_overrides))
    return _validate(data, source="configuration files")
