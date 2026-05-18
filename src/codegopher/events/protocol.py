"""Typed JSONL protocol payloads for CodeGopher event streams."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

PROTOCOL_VERSION = 1


class ProtocolModel(BaseModel):
    """Base shape shared by all CodeGopher JSONL protocol messages."""

    model_config = ConfigDict(extra="forbid")

    version: Literal[1] = PROTOCOL_VERSION
    type: str = Field(min_length=1)
    session_id: str | None = None
    turn_id: str | None = None
