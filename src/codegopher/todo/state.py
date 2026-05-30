"""In-memory session TODO state."""

from __future__ import annotations

import builtins
from collections.abc import Callable
from datetime import UTC, datetime
from uuid import uuid4

from codegopher.core.types import TodoItem, TodoStatus


class TodoState:
    """Mutable TODO list for one CodeGopher session."""

    def __init__(
        self,
        items: builtins.list[TodoItem] | None = None,
        *,
        max_items: int = 100,
        enforce_single_in_progress: bool = True,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self.max_items = max_items
        self.enforce_single_in_progress = enforce_single_in_progress
        self._now = now or (lambda: datetime.now(UTC))
        self.items: builtins.list[TodoItem] = list(items or [])

    @classmethod
    def from_raw(
        cls,
        raw_items: object,
        *,
        max_items: int = 100,
        enforce_single_in_progress: bool = True,
        now: Callable[[], datetime] | None = None,
    ) -> TodoState:
        if not isinstance(raw_items, list):
            raise ValueError("TODO items must be a list")
        return cls(
            [TodoItem.model_validate(raw_item) for raw_item in raw_items],
            max_items=max_items,
            enforce_single_in_progress=enforce_single_in_progress,
            now=now,
        )

    def add(
        self,
        text: str,
        *,
        status: TodoStatus = "pending",
        source: str | None = None,
        reason: str | None = None,
        related_files: builtins.list[str] | None = None,
        evidence_refs: builtins.list[str] | None = None,
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
            reason=_normalize_optional(reason),
            related_files=_normalize_list(related_files),
            evidence_refs=_normalize_list(evidence_refs),
            created_at=now,
            updated_at=now,
        )
        if status == "in_progress":
            self._clear_existing_in_progress(except_id=item.id)
        self.items.append(item)
        return item

    def update(
        self,
        item_id: str,
        *,
        text: str | None = None,
        status: TodoStatus | None = None,
        reason: str | None = None,
        related_files: builtins.list[str] | None = None,
        evidence_refs: builtins.list[str] | None = None,
    ) -> TodoItem:
        for index, item in enumerate(self.items):
            if item.id == item_id:
                payload = item.model_dump()
                if text is not None:
                    normalized_text = text.strip()
                    if not normalized_text:
                        raise ValueError("TODO text is required")
                    payload["text"] = normalized_text
                if status is not None:
                    payload["status"] = status
                if reason is not None:
                    payload["reason"] = _normalize_optional(reason)
                if related_files is not None:
                    payload["related_files"] = _normalize_list(related_files)
                if evidence_refs is not None:
                    payload["evidence_refs"] = _normalize_list(evidence_refs)
                payload["updated_at"] = self._now()
                updated = TodoItem.model_validate(payload)
                if updated.status == "in_progress":
                    self._clear_existing_in_progress(except_id=updated.id)
                self.items[index] = updated
                return updated
        raise KeyError(item_id)

    def set_status(
        self,
        item_id: str,
        status: TodoStatus,
        *,
        reason: str | None = None,
    ) -> TodoItem:
        return self.update(item_id, status=status, reason=reason)

    def done(self, item_id: str) -> TodoItem:
        return self.set_status(item_id, "done")

    def list(self, *, include_done: bool = True) -> builtins.list[TodoItem]:
        if include_done:
            return list(self.items)
        return [item for item in self.items if item.status != "done"]

    def context_items(self) -> builtins.list[str]:
        lines = []
        for item in self.list(include_done=False):
            if item.status == "cancelled":
                continue
            detail = f"[{item.id}] {item.status}: {item.text}"
            parts = []
            if item.reason:
                parts.append(f"reason={item.reason}")
            if item.related_files:
                parts.append("files=" + ", ".join(item.related_files[:5]))
            if item.evidence_refs:
                parts.append("evidence=" + ", ".join(item.evidence_refs[:5]))
            if parts:
                detail += " (" + "; ".join(parts) + ")"
            lines.append(detail)
        return lines

    def to_jsonable(self) -> builtins.list[dict[str, object]]:
        return [item.model_dump(mode="json") for item in self.items]

    def _item_id(self) -> str:
        return f"todo-{uuid4().hex[:8]}"

    def _clear_existing_in_progress(self, *, except_id: str) -> None:
        if not self.enforce_single_in_progress:
            return
        now = self._now()
        for index, item in enumerate(self.items):
            if item.id == except_id or item.status != "in_progress":
                continue
            self.items[index] = item.model_copy(
                update={"status": "pending", "updated_at": now}
            )


def _normalize_optional(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _normalize_list(values: builtins.list[str] | None) -> builtins.list[str]:
    if values is None:
        return []
    normalized: builtins.list[str] = []
    for value in values:
        item = str(value).strip()
        if item and item not in normalized:
            normalized.append(item)
    return normalized
