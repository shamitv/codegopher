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
    replay_reasoning_content: bool | None = None
    approval_mode: str | None = None
    max_iterations: int | None = None
    max_output_tokens: int | None = None
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


def _ensure_selected_provider_entry(data: dict[str, Any]) -> dict[str, Any]:
    model = data.setdefault("model", {})
    provider = str(model.get("provider", "openai"))
    name = str(model.get("name", "gpt-4o"))
    providers = data.setdefault("providers", {})
    entries = providers.setdefault(provider, [])
    for entry in entries:
        if str(entry.get("id")) == name:
            return cast("dict[str, Any]", entry)
    selected_entry = {"id": name, "name": name}
    entries.append(selected_entry)
    return selected_entry


def _env_overrides(environ: Mapping[str, str]) -> dict[str, Any]:
    data: dict[str, Any] = {}
    if model := environ.get("CODEGOPHER_MODEL"):
        data = _merge(data, {"model": {"name": model}})
    if provider := environ.get("CODEGOPHER_PROVIDER"):
        data = _merge(data, {"model": {"provider": provider}})
    if max_output_tokens := environ.get("CODEGOPHER_MAX_OUTPUT_TOKENS"):
        data = _merge(data, {"model": {"max_output_tokens": max_output_tokens}})
    if approval_mode := environ.get("CODEGOPHER_APPROVAL_MODE"):
        data["approval_mode"] = approval_mode
    if debug := environ.get("CODEGOPHER_DEBUG"):
        data["debug"] = debug.lower() in {"1", "true", "yes", "on"}
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
    if overrides.max_output_tokens is not None:
        data = _merge(
            data,
            {"model": {"max_output_tokens": overrides.max_output_tokens}},
        )
    if overrides.debug is not None:
        data["debug"] = overrides.debug
    return data


def _env_provider_overrides(environ: Mapping[str, str]) -> dict[str, Any]:
    overrides: dict[str, Any] = {}
    if base_url := environ.get("CODEGOPHER_BASE_URL"):
        overrides["base_url"] = base_url
    if api_family := environ.get("CODEGOPHER_API_FAMILY"):
        overrides["api_family"] = api_family
    if api_key_env := environ.get("CODEGOPHER_API_KEY_ENV"):
        overrides["api_key_env"] = api_key_env
    if replay_reasoning_content := environ.get("CODEGOPHER_REPLAY_REASONING_CONTENT"):
        overrides["replay_reasoning_content"] = replay_reasoning_content.lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
    return overrides


def _cli_provider_overrides(overrides: CliOverrides | None) -> dict[str, Any]:
    if overrides is None:
        return {}
    data: dict[str, Any] = {}
    if overrides.base_url:
        data["base_url"] = overrides.base_url
    if overrides.api_family:
        data["api_family"] = overrides.api_family
    if overrides.replay_reasoning_content is not None:
        data["replay_reasoning_content"] = overrides.replay_reasoning_content
    return data


def _apply_provider_overrides(data: dict[str, Any], overrides: Mapping[str, Any]) -> None:
    if not overrides:
        return
    entry = _ensure_selected_provider_entry(data)
    entry.update(overrides)


def _has_cli_overrides(overrides: CliOverrides | None) -> bool:
    return overrides is not None and any(
        (
            overrides.model,
            overrides.provider,
            overrides.base_url,
            overrides.api_family,
            overrides.replay_reasoning_content is not None,
            overrides.approval_mode,
            overrides.max_iterations is not None,
            overrides.max_output_tokens is not None,
            overrides.debug is not None,
        )
    )


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
    env_provider_config = _env_provider_overrides(env)
    cli_provider_config = _cli_provider_overrides(cli_overrides)

    data: dict[str, Any] = {}
    data = _merge(data, home_config)
    data = _merge(data, project_config)
    data = _merge(data, env_config)
    data = _merge(data, cli_config)
    _apply_provider_overrides(data, env_provider_config)
    _apply_provider_overrides(data, cli_provider_config)
    if api_key_env := env_provider_config.get("api_key_env"):
        _apply_provider_overrides(data, {"api_key_env": api_key_env})

    has_env_overrides = bool(env_config or env_provider_config)
    has_cli_overrides = _has_cli_overrides(cli_overrides)

    sources: list[str] = []
    if home_config or project_config:
        sources.append("configuration files")
    if has_env_overrides:
        sources.append("environment variables")
    if has_cli_overrides:
        sources.append("CLI overrides")

    source_labels = ["defaults"]
    if home_config:
        source_labels.append("user")
    if project_config:
        source_labels.append("project")
    if has_env_overrides:
        source_labels.append("environment")
    if has_cli_overrides:
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
