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


def test_memory_store_session_file_is_keyed_by_session_id(tmp_path: Path) -> None:
    store = MemoryStore(data_home=tmp_path / "data")

    first = store.session_file("session-1")
    second = store.session_file("session-2")

    assert first.parent == store.session_dir
    assert first.name.endswith(".json")
    assert first != second


def test_memory_store_rejects_empty_session_id(tmp_path: Path) -> None:
    store = MemoryStore(data_home=tmp_path / "data")

    try:
        store.session_file("")
    except ValueError as exc:
        assert "session_id is required" in str(exc)
    else:
        raise AssertionError("empty session id was accepted")


def test_memory_store_project_file_is_keyed_by_canonical_cwd(tmp_path: Path) -> None:
    store = MemoryStore(data_home=tmp_path / "data")
    project = tmp_path / "project"
    project.mkdir()

    direct = store.project_file(project)
    relative = store.project_file(project / ".." / "project")

    assert direct.parent == store.project_dir
    assert direct.name.endswith(".json")
    assert direct == relative


def test_memory_store_different_projects_have_different_files(tmp_path: Path) -> None:
    store = MemoryStore(data_home=tmp_path / "data")
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()

    assert store.project_file(first) != store.project_file(second)
