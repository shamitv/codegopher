from __future__ import annotations

from pathlib import Path

from codegopher.memory import EpisodeState
from codegopher.tools.base import ToolResult


def test_episode_state_records_file_reads_with_relative_refs(tmp_path: Path) -> None:
    state = EpisodeState()

    state.record_tool_result(
        {
            "id": "call-1",
            "name": "read_file",
            "arguments": {"path": str(tmp_path / "app.py")},
        },
        ToolResult(tool_call_id="call-1", content="one\ntwo\n"),
        cwd=tmp_path,
    )

    assert state.context_items()[0].endswith("refs=app.py")
    assert "Read " in state.context_items()[0]


def test_episode_state_redacts_urls_temp_paths_and_secrets(tmp_path: Path) -> None:
    state = EpisodeState()

    state.add(
        "note",
        "Saw http://localhost:8080 and /tmp/raw token=abc123",
        refs=["/tmp/raw/app.py"],
    )

    item = state.context_items()[0]
    assert "http://localhost:8080" not in item
    assert "/tmp/raw" not in item
    assert "abc123" not in item
    assert "[URL]" in item
    assert "[TMP_PATH]" in item
    assert "token=[REDACTED]" in item


def test_episode_state_records_todo_metadata_as_task_observation() -> None:
    state = EpisodeState()

    state.record_tool_result(
        {
            "id": "call-1",
            "name": "update_todo",
            "arguments": {
                "action": "block",
                "id": "todo-1",
                "reason": "missing sink evidence",
                "related_files": ["app.py"],
                "evidence_refs": ["app.py:10"],
            },
        },
        ToolResult(tool_call_id="call-1", content="Updated TODO todo-1 to blocked"),
        cwd=Path("."),
    )

    item = state.context_items()[0]
    assert "todo_update: TODO block: todo-1 reason=missing sink evidence" in item
    assert "refs=app.py, app.py:10" in item


def test_episode_state_keeps_bounded_recent_entries() -> None:
    state = EpisodeState(max_entries=2)

    state.add("note", "one")
    state.add("note", "two")
    state.add("note", "three")

    items = state.context_items()
    assert len(items) == 2
    assert "one" not in "\n".join(items)
    assert "three" in items[-1]
