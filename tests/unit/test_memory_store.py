from __future__ import annotations

from datetime import UTC, datetime, timedelta
import json
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


def test_memory_store_adds_and_lists_session_entries(tmp_path: Path) -> None:
    clock = FakeClock(datetime(2026, 5, 17, tzinfo=UTC))
    store = MemoryStore(data_home=tmp_path / "data", now=clock)

    entry = store.add_entry(
        "session",
        session_id="session-1",
        content="remember this",
        source="user",
        tags=["alpha"],
    )

    entries = store.list_entries("session", session_id="session-1")
    assert entry.id.startswith("mem-")
    assert entries == [entry]
    assert entries[0].created_at == datetime(2026, 5, 17, tzinfo=UTC)
    assert entries[0].updated_at == datetime(2026, 5, 17, tzinfo=UTC)
    assert entries[0].tags == ["alpha"]


def test_memory_store_updates_and_deletes_project_entries(tmp_path: Path) -> None:
    clock = FakeClock(datetime(2026, 5, 17, tzinfo=UTC))
    store = MemoryStore(data_home=tmp_path / "data", now=clock)
    project = tmp_path / "project"
    project.mkdir()
    entry = store.add_entry("project", cwd=project, content="old")

    updated = store.update_entry("project", entry.id, cwd=project, content="new")
    deleted = store.delete_entry("project", entry.id, cwd=project)

    assert updated.id == entry.id
    assert updated.created_at == entry.created_at
    assert updated.updated_at > entry.updated_at
    assert updated.content == "new"
    assert deleted is True
    assert store.list_entries("project", cwd=project) == []


def test_memory_store_enforces_limits(tmp_path: Path) -> None:
    store = MemoryStore(data_home=tmp_path / "data")

    try:
        store.add_entry("session", session_id="s", content="abcdef", max_entry_chars=5)
    except ValueError as exc:
        assert "max_entry_chars" in str(exc)
    else:
        raise AssertionError("oversized memory was accepted")

    store.add_entry("session", session_id="s", content="one", max_entries=1)
    try:
        store.add_entry("session", session_id="s", content="two", max_entries=1)
    except ValueError as exc:
        assert "max_entries" in str(exc)
    else:
        raise AssertionError("scope limit was not enforced")


def test_memory_store_redacts_api_keys_and_raw_secret_env_values(tmp_path: Path) -> None:
    store = MemoryStore(
        data_home=tmp_path / "data",
        environ={
            "OPENAI_API_KEY": "raw-secret-value",
            "NORMAL_VALUE": "not-redacted",
        },
    )

    entry = store.add_entry(
        "session",
        session_id="session-1",
        content="api_key=inline-secret and raw-secret-value but not-redacted",
    )
    raw = store.session_file("session-1").read_text(encoding="utf-8")
    data = json.loads(raw)

    assert "inline-secret" not in raw
    assert "raw-secret-value" not in raw
    assert "not-redacted" in raw
    assert "[REDACTED]" in entry.content
    assert "[REDACTED]" in data["entries"][0]["content"]


class FakeClock:
    def __init__(self, value: datetime) -> None:
        self.value = value

    def __call__(self) -> datetime:
        current = self.value
        self.value = self.value + timedelta(seconds=1)
        return current
