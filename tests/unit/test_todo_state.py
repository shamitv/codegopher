from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from codegopher.todo import TodoState


def test_todo_state_adds_items_with_stable_shape() -> None:
    clock = FakeClock(datetime(2026, 5, 17, tzinfo=UTC))
    state = TodoState(now=clock)

    item = state.add(" write tests ", source="user")

    assert item.id.startswith("todo-")
    assert item.text == "write tests"
    assert item.status == "pending"
    assert item.source == "user"
    assert item.created_at == datetime(2026, 5, 17, tzinfo=UTC)
    assert state.list() == [item]


def test_todo_state_updates_status_and_done() -> None:
    clock = FakeClock(datetime(2026, 5, 17, tzinfo=UTC))
    state = TodoState(now=clock)
    item = state.add("write tests")

    in_progress = state.set_status(item.id, "in_progress")
    done = state.done(item.id)

    assert in_progress.status == "in_progress"
    assert done.status == "done"
    assert done.updated_at > item.updated_at


def test_todo_state_context_includes_only_active_items() -> None:
    state = TodoState()
    active = state.add("write tests")
    complete = state.add("update docs")
    state.done(complete.id)

    assert state.context_items() == [f"[{active.id}] pending: write tests"]


def test_todo_state_rejects_empty_text_and_limit() -> None:
    state = TodoState(max_items=1)

    with pytest.raises(ValueError, match="text"):
        state.add(" ")

    state.add("one")
    with pytest.raises(ValueError, match="limit"):
        state.add("two")


def test_todo_state_rejects_missing_and_invalid_status() -> None:
    state = TodoState()

    with pytest.raises(KeyError):
        state.done("missing")

    item = state.add("one")
    with pytest.raises(ValidationError):
        state.set_status(item.id, "blocked")  # type: ignore[arg-type]


def test_todo_state_round_trips_jsonable_items() -> None:
    state = TodoState()
    state.add("write tests")

    restored = TodoState.from_raw(state.to_jsonable())

    assert restored.list()[0].text == "write tests"
    assert restored.list()[0].status == "pending"


class FakeClock:
    def __init__(self, value: datetime) -> None:
        self.value = value

    def __call__(self) -> datetime:
        current = self.value
        self.value = self.value + timedelta(seconds=1)
        return current
