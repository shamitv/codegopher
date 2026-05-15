from __future__ import annotations

import codegopher


def test_package_import_exposes_version() -> None:
    assert codegopher.__version__ == "0.1.0"

