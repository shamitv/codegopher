from __future__ import annotations

from app import greet


def test_greet_uses_supplied_name() -> None:
    assert greet("Ada") == "Hello, Ada!"

