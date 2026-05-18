from __future__ import annotations

import pytest
from pydantic import ValidationError

from codegopher.events.protocol import PROTOCOL_VERSION, ProtocolModel


def test_protocol_model_defaults_common_fields() -> None:
    payload = ProtocolModel(type="test_message")

    assert payload.version == PROTOCOL_VERSION
    assert payload.type == "test_message"
    assert payload.session_id is None
    assert payload.turn_id is None


def test_protocol_model_accepts_common_ids() -> None:
    payload = ProtocolModel(
        type="test_message",
        session_id="session-1",
        turn_id="turn-1",
    )

    assert payload.session_id == "session-1"
    assert payload.turn_id == "turn-1"


def test_protocol_model_rejects_unsupported_version() -> None:
    with pytest.raises(ValidationError):
        ProtocolModel.model_validate({"version": 2, "type": "test_message"})


def test_protocol_model_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        ProtocolModel.model_validate({"type": "test_message", "extra": True})


def test_protocol_model_rejects_blank_type() -> None:
    with pytest.raises(ValidationError):
        ProtocolModel(type="")
