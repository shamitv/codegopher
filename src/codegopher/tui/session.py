"""Local TUI session persistence."""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from codegopher.config.schema import Settings
from codegopher.core.types import Message, TodoItem
from codegopher.utils.paths import canonical_path

SESSION_VERSION = 4
COMPATIBLE_SESSION_VERSIONS = {1, 2, 3, SESSION_VERSION}
MessageRole = Literal["user", "assistant", "system"]


@dataclass(frozen=True)
class SessionMessage:
    role: MessageRole
    content: str


@dataclass
class TuiSessionState:
    session_id: str
    created_at: str
    updated_at: str
    cwd: str
    provider: str
    model: str
    approval_mode: str
    messages: list[SessionMessage] = field(default_factory=list)
    provider_messages: list[Message] = field(default_factory=list)
    loaded_skill_ids: list[str] = field(default_factory=list)
    todo_items: list[TodoItem] = field(default_factory=list)


@dataclass(frozen=True)
class SessionLoadResult:
    state: TuiSessionState | None
    error: str | None = None


class TuiSessionStore:
    """JSON session storage rooted in CodeGopher's user data directory."""

    def __init__(
        self,
        *,
        data_home: Path,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self.data_home = data_home
        self.sessions_dir = data_home / "sessions"
        self._now = now or (lambda: datetime.now(UTC))

    @classmethod
    def default(
        cls,
        *,
        environ: Mapping[str, str] | None = None,
        home: Path | None = None,
    ) -> TuiSessionStore:
        env = os.environ if environ is None else environ
        if data_home := env.get("CODEGOPHER_DATA_HOME"):
            root = Path(data_home)
        elif xdg_data_home := env.get("XDG_DATA_HOME"):
            root = Path(xdg_data_home) / "codegopher"
        else:
            root = (home or Path.home()) / ".local" / "share" / "codegopher"
        return cls(data_home=root)

    def create(self, *, cwd: Path, settings: Settings) -> TuiSessionState:
        now = self._timestamp()
        return TuiSessionState(
            session_id=f"{self._cwd_key(cwd)}-{uuid4().hex[:12]}",
            created_at=now,
            updated_at=now,
            cwd=canonical_path(cwd),
            provider=settings.model.provider,
            model=settings.model.name,
            approval_mode=settings.approval_mode.value,
            messages=[],
        )

    def load_latest(self, *, cwd: Path) -> SessionLoadResult:
        candidates = sorted(
            self.sessions_dir.glob(f"{self._cwd_key(cwd)}-*.json"),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        if not candidates:
            return SessionLoadResult(state=None)

        path = candidates[0]
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            state = self._decode_state(data, expected_cwd=canonical_path(cwd))
        except Exception as exc:
            return SessionLoadResult(
                state=None,
                error=f"Could not resume session {path.name}: {exc}",
            )
        return SessionLoadResult(state=state)

    def save(self, state: TuiSessionState, *, settings: Settings) -> Path:
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        state.updated_at = self._timestamp()
        state.provider = settings.model.provider
        state.model = settings.model.name
        state.approval_mode = settings.approval_mode.value
        path = self.sessions_dir / f"{state.session_id}.json"
        path.write_text(json.dumps(self._encode_state(state), indent=2), encoding="utf-8")
        return path

    def _timestamp(self) -> str:
        return self._now().astimezone(UTC).isoformat()

    def _cwd_key(self, cwd: Path) -> str:
        digest = hashlib.sha256(canonical_path(cwd).encode("utf-8")).hexdigest()
        return digest[:16]

    def _encode_state(self, state: TuiSessionState) -> dict[str, Any]:
        return {
            "version": SESSION_VERSION,
            "session_id": state.session_id,
            "created_at": state.created_at,
            "updated_at": state.updated_at,
            "metadata": {
                "cwd": state.cwd,
                "provider": state.provider,
                "model": state.model,
                "approval_mode": state.approval_mode,
            },
            "messages": [
                {"role": message.role, "content": message.content}
                for message in state.messages
            ],
            "provider_messages": state.provider_messages,
            "loaded_skill_ids": state.loaded_skill_ids,
            "todo_items": [item.model_dump(mode="json") for item in state.todo_items],
        }

    def _decode_state(self, data: Any, *, expected_cwd: str) -> TuiSessionState:
        if not isinstance(data, dict):
            raise ValueError("session root must be an object")
        version = data.get("version")
        if version not in COMPATIBLE_SESSION_VERSIONS:
            raise ValueError("incompatible session version")
        metadata = data.get("metadata")
        if not isinstance(metadata, dict):
            raise ValueError("missing session metadata")
        cwd = str(metadata.get("cwd", ""))
        if cwd != expected_cwd:
            raise ValueError("session cwd does not match current cwd")

        messages: list[SessionMessage] = []
        raw_messages = data.get("messages", [])
        if not isinstance(raw_messages, list):
            raise ValueError("session messages must be a list")
        for raw_message in raw_messages:
            if not isinstance(raw_message, dict):
                raise ValueError("session message must be an object")
            role = raw_message.get("role")
            if role not in {"user", "assistant", "system"}:
                raise ValueError("session message role is invalid")
            content = raw_message.get("content")
            if not isinstance(content, str):
                raise ValueError("session message content must be a string")
            messages.append(SessionMessage(role=role, content=content))

        provider_messages = (
            []
            if version == 1 and "provider_messages" not in data
            else self._decode_provider_messages(data.get("provider_messages", []))
        )
        loaded_skill_ids = self._decode_loaded_skill_ids(data.get("loaded_skill_ids", []))
        todo_items = self._decode_todo_items(data.get("todo_items", []))

        return TuiSessionState(
            session_id=str(data.get("session_id", ""))
            or f"{self._cwd_key(Path(cwd))}-{uuid4().hex[:12]}",
            created_at=str(data.get("created_at", "")),
            updated_at=str(data.get("updated_at", "")),
            cwd=cwd,
            provider=str(metadata.get("provider", "")),
            model=str(metadata.get("model", "")),
            approval_mode=str(metadata.get("approval_mode", "")),
            messages=messages,
            provider_messages=provider_messages,
            loaded_skill_ids=loaded_skill_ids,
            todo_items=todo_items,
        )

    def _decode_provider_messages(self, raw_messages: Any) -> list[Message]:
        if not isinstance(raw_messages, list):
            raise ValueError("provider messages must be a list")

        messages: list[Message] = []
        for raw_message in raw_messages:
            if not isinstance(raw_message, dict):
                raise ValueError("provider message must be an object")
            role = raw_message.get("role")
            if role not in {"system", "user", "assistant", "tool"}:
                raise ValueError("provider message role is invalid")
            content = raw_message.get("content")
            if content is not None and not isinstance(content, str):
                raise ValueError("provider message content must be a string or null")
            message: Message = {"role": role, "content": content}
            if name := raw_message.get("name"):
                if not isinstance(name, str):
                    raise ValueError("provider message name must be a string")
                message["name"] = name
            if tool_call_id := raw_message.get("tool_call_id"):
                if not isinstance(tool_call_id, str):
                    raise ValueError("provider message tool_call_id must be a string")
                message["tool_call_id"] = tool_call_id
            if "tool_calls" in raw_message:
                tool_calls = raw_message["tool_calls"]
                if not isinstance(tool_calls, list):
                    raise ValueError("provider message tool_calls must be a list")
                message["tool_calls"] = tool_calls
            if "response_items" in raw_message:
                response_items = raw_message["response_items"]
                if not isinstance(response_items, list) or not all(
                    isinstance(item, dict) for item in response_items
                ):
                    raise ValueError("provider message response_items must be a list of objects")
                message["response_items"] = response_items
            if "reasoning_content" in raw_message:
                reasoning_content = raw_message["reasoning_content"]
                if not isinstance(reasoning_content, str):
                    raise ValueError("provider message reasoning_content must be a string")
                message["reasoning_content"] = reasoning_content
            messages.append(message)
        return messages

    def _decode_loaded_skill_ids(self, raw_skill_ids: Any) -> list[str]:
        if not isinstance(raw_skill_ids, list):
            raise ValueError("loaded skill ids must be a list")
        skill_ids: list[str] = []
        for raw_skill_id in raw_skill_ids:
            if not isinstance(raw_skill_id, str):
                raise ValueError("loaded skill id must be a string")
            if raw_skill_id not in skill_ids:
                skill_ids.append(raw_skill_id)
        return skill_ids

    def _decode_todo_items(self, raw_items: Any) -> list[TodoItem]:
        if not isinstance(raw_items, list):
            raise ValueError("todo items must be a list")
        items: list[TodoItem] = []
        for raw_item in raw_items:
            if not isinstance(raw_item, dict):
                raise ValueError("todo item must be an object")
            try:
                items.append(TodoItem.model_validate(raw_item))
            except Exception as exc:
                raise ValueError(f"todo item is invalid: {exc}") from exc
        return items
