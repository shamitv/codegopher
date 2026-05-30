"""JSON helpers for provider and tool payloads."""

from __future__ import annotations

import json
from typing import Any

from codegopher.core.errors import CodeGopherError


class JsonPayloadError(CodeGopherError):
    """Raised when a JSON payload cannot be decoded or serialized."""

    def __init__(
        self,
        message: str,
        *,
        source: str = "payload",
        decoder_message: str | None = None,
        line: int | None = None,
        column: int | None = None,
        position: int | None = None,
        payload_length: int | None = None,
    ) -> None:
        super().__init__(message)
        self.source = source
        self.decoder_message = decoder_message
        self.line = line
        self.column = column
        self.position = position
        self.payload_length = payload_length

    def to_metadata(self) -> dict[str, int | str | None]:
        return {
            "source": self.source,
            "decoder_message": self.decoder_message,
            "line": self.line,
            "column": self.column,
            "position": self.position,
            "payload_length": self.payload_length,
        }


def loads_object(payload: str, *, source: str = "payload") -> dict[str, Any]:
    try:
        value = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise JsonPayloadError(
            (
                f"Malformed JSON in {source}: {exc.msg} "
                f"(line {exc.lineno}, column {exc.colno}, position {exc.pos}, "
                f"length {len(payload)})"
            ),
            source=source,
            decoder_message=exc.msg,
            line=exc.lineno,
            column=exc.colno,
            position=exc.pos,
            payload_length=len(payload),
        ) from exc
    if not isinstance(value, dict):
        raise JsonPayloadError(f"Expected JSON object in {source}")
    return value


def dumps_json(value: Any) -> str:
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except TypeError as exc:
        raise JsonPayloadError(f"Value is not JSON serializable: {exc}") from exc
