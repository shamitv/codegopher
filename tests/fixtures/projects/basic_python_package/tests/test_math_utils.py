from __future__ import annotations

from sample_pkg.math_utils import add, double


def test_add() -> None:
    assert add(2, 3) == 5


def test_double() -> None:
    assert double(4) == 8

