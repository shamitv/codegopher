from __future__ import annotations

import pytest

from codegopher.utils.json import JsonPayloadError, dumps_json, loads_object


def test_loads_object_rejects_malformed_json() -> None:
    with pytest.raises(JsonPayloadError, match="line 1, column 2") as exc_info:
        loads_object("{", source="tool arguments")
    assert exc_info.value.to_metadata()["position"] == 1
    assert exc_info.value.to_metadata()["payload_length"] == 1


def test_loads_object_rejects_non_object_json() -> None:
    with pytest.raises(JsonPayloadError, match="Expected JSON object"):
        loads_object("[]")


def test_dumps_json_rejects_unserializable_value() -> None:
    with pytest.raises(JsonPayloadError, match="not JSON serializable"):
        dumps_json(object())
