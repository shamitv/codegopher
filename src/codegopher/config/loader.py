"""Settings loader."""

from __future__ import annotations

from codegopher.config.schema import Settings


def load_settings() -> Settings:
    return Settings()

