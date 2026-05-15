"""JSON helpers for provider and tool payloads."""

from __future__ import annotations

import json
from typing import Any

from codegopher.core.errors import CodeGopherError


class JsonPayloadError(CodeGopherError):
    """Raised when a JSON payload cannot be decoded or serialized."""


def loads_object(payload: str, *, source: str = "payload") -> dict[str, Any]:
    try:
        value = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise JsonPayloadError(f"Malformed JSON in {source}: {exc.msg}") from exc
    if not isinstance(value, dict):
        raise JsonPayloadError(f"Expected JSON object in {source}")
    return value


def dumps_json(value: Any) -> str:
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except TypeError as exc:
        raise JsonPayloadError(f"Value is not JSON serializable: {exc}") from exc

