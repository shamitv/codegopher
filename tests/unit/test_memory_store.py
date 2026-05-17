from __future__ import annotations

from pathlib import Path

from codegopher.memory import MemoryStore


def test_memory_store_roots_under_data_home(tmp_path: Path) -> None:
    store = MemoryStore(data_home=tmp_path / "data")

    assert store.data_home == tmp_path / "data"
    assert store.memory_root == tmp_path / "data" / "memory"
    assert store.session_dir == tmp_path / "data" / "memory" / "session"
    assert store.project_dir == tmp_path / "data" / "memory" / "project"


def test_memory_store_default_uses_codegopher_data_home(tmp_path: Path) -> None:
    store = MemoryStore.default(environ={"CODEGOPHER_DATA_HOME": str(tmp_path / "custom")})

    assert store.data_home == tmp_path / "custom"


def test_memory_store_default_uses_xdg_data_home(tmp_path: Path) -> None:
    store = MemoryStore.default(environ={"XDG_DATA_HOME": str(tmp_path / "xdg")})

    assert store.data_home == tmp_path / "xdg" / "codegopher"
