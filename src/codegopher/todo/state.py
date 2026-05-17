"""In-memory session TODO state."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from uuid import uuid4

from codegopher.core.types import TodoItem, TodoStatus


class TodoState:
    """Mutable TODO list for one CodeGopher session."""

    def __init__(
        self,
        items: list[TodoItem] | None = None,
        *,
        max_items: int = 100,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self.max_items = max_items
        self._now = now or (lambda: datetime.now(UTC))
        self.items: list[TodoItem] = list(items or [])

    @classmethod
    def from_raw(
        cls,
        raw_items: object,
        *,
        max_items: int = 100,
        now: Callable[[], datetime] | None = None,
    ) -> TodoState:
        if not isinstance(raw_items, list):
            raise ValueError("TODO items must be a list")
        return cls(
            [TodoItem.model_validate(raw_item) for raw_item in raw_items],
            max_items=max_items,
            now=now,
        )

    def add(
        self,
        text: str,
        *,
        status: TodoStatus = "pending",
        source: str | None = None,
    ) -> TodoItem:
        normalized = text.strip()
        if not normalized:
            raise ValueError("TODO text is required")
        if len(self.items) >= self.max_items:
            raise ValueError("TODO item limit reached")
        now = self._now()
        item = TodoItem(
            id=self._item_id(),
            text=normalized,
            status=status,
            source=source,
            created_at=now,
            updated_at=now,
        )
        self.items.append(item)
        return item

    def set_status(self, item_id: str, status: TodoStatus) -> TodoItem:
        for index, item in enumerate(self.items):
            if item.id == item_id:
                updated = TodoItem.model_validate(
                    {
                        **item.model_dump(),
                        "status": status,
                        "updated_at": self._now(),
                    }
                )
                self.items[index] = updated
                return updated
        raise KeyError(item_id)

    def done(self, item_id: str) -> TodoItem:
        return self.set_status(item_id, "done")

    def list(self, *, include_done: bool = True) -> list[TodoItem]:
        if include_done:
            return list(self.items)
        return [item for item in self.items if item.status != "done"]

    def context_items(self) -> list[str]:
        return [
            f"[{item.id}] {item.status}: {item.text}"
            for item in self.list(include_done=False)
        ]

    def to_jsonable(self) -> list[dict[str, object]]:
        return [item.model_dump(mode="json") for item in self.items]

    def _item_id(self) -> str:
        return f"todo-{uuid4().hex[:8]}"
