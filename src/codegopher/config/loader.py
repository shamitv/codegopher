"""Settings loader."""

from __future__ import annotations

import copy
import tomllib
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from codegopher.core.errors import ConfigurationError
from codegopher.config.schema import Settings


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


def load_settings(*, home: Path | None = None) -> Settings:
    home_root = home or Path.home()
    data: dict[str, Any] = {}
    data = _merge(data, _load_toml(home_root / ".codegopher" / "settings.toml"))
    return _validate(data, source="configuration files")
