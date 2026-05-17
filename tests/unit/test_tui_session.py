from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
from textual.widgets import Input

import codegopher.tui.launcher as launcher
from codegopher.config.schema import ApprovalMode, ModelConfig, ProviderEntry, Settings
from codegopher.core.types import TodoItem
from codegopher.memory import MemoryStore
from codegopher.providers.mock import MockProvider
from codegopher.tui import CodeGopherApp
from codegopher.tui.session import (
    SESSION_VERSION,
    SessionMessage,
    TuiSessionState,
    TuiSessionStore,
)
from codegopher.utils.paths import canonical_path


def make_settings() -> Settings:
    return Settings(
        model=ModelConfig(provider="openai", name="test-model"),
        providers={
            "openai": [
                ProviderEntry(
                    id="test-model",
                    name="Test Model",
                    api_key_env="SECRET_API_KEY",
                )
            ]
        },
        approval_mode=ApprovalMode.yolo,
    )


def make_store(tmp_path: Path) -> TuiSessionStore:
    clock = FakeClock(datetime(2026, 5, 15, tzinfo=UTC))
    return TuiSessionStore(data_home=tmp_path / "data", now=clock)


async def submit(app: CodeGopherApp, pilot: Any, value: str, *, pause: float = 0.1) -> None:
    input_widget = app.query_one("#prompt-input", Input)
    input_widget.focus()
    input_widget.value = value
    await pilot.press("enter")
    await pilot.pause(pause)


def read_session_json(store: TuiSessionStore, state: TuiSessionState) -> dict[str, Any]:
    path = store.sessions_dir / f"{state.session_id}.json"
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.mark.asyncio
async def test_tui_session_persists_completed_turn_messages_and_metadata(tmp_path: Path) -> None:
    store = make_store(tmp_path)
    provider = MockProvider([[{"type": "text_delta", "content": "answer"}, {"type": "done"}]])
    app = CodeGopherApp(
        settings=make_settings(),
        cwd=tmp_path,
        provider_factory=lambda _settings: provider,
        session_store=store,
    )

    async with app.run_test() as pilot:
        await submit(app, pilot, "question")

    assert app.session_state is not None
    data = read_session_json(store, app.session_state)
    assert data["version"] == SESSION_VERSION
    assert data["metadata"]["cwd"] == canonical_path(tmp_path)
    assert data["metadata"]["provider"] == "openai"
    assert data["metadata"]["model"] == "test-model"
    assert data["metadata"]["approval_mode"] == "yolo"
    assert data["messages"][-2:] == [
        {"role": "user", "content": "You: question"},
        {"role": "assistant", "content": "Assistant: answer"},
    ]
    assert data["provider_messages"] == [
        {"role": "user", "content": "question"},
        {"role": "assistant", "content": "answer"},
    ]
    assert data["loaded_skill_ids"] == []
    assert data["todo_items"] == []


@pytest.mark.asyncio
async def test_tui_session_persists_tool_and_shell_summaries(tmp_path: Path) -> None:
    store = make_store(tmp_path)
    provider = MockProvider([[{"type": "text_delta", "content": "unused"}, {"type": "done"}]])
    app = CodeGopherApp(
        settings=make_settings(),
        cwd=tmp_path,
        provider_factory=lambda _settings: provider,
        session_store=store,
    )

    async with app.run_test() as pilot:
        await submit(app, pilot, "/shell printf shell-output")
        for _ in range(20):
            if not app.turn_running:
                break
            await pilot.pause(0.05)

    assert app.session_state is not None
    data = read_session_json(store, app.session_state)
    contents = [message["content"] for message in data["messages"]]
    assert any(content.startswith("Shell requested:") for content in contents)
    assert any("shell-output" in content for content in contents)


def test_tui_session_default_data_home_uses_environment(tmp_path: Path) -> None:
    store = TuiSessionStore.default(environ={"CODEGOPHER_DATA_HOME": str(tmp_path / "custom")})
    assert store.data_home == tmp_path / "custom"

    xdg_store = TuiSessionStore.default(environ={"XDG_DATA_HOME": str(tmp_path / "xdg")})
    assert xdg_store.data_home == tmp_path / "xdg" / "codegopher"


def test_tui_session_does_not_persist_api_keys_or_environment_values(tmp_path: Path) -> None:
    store = make_store(tmp_path)
    state = store.create(cwd=tmp_path, settings=make_settings())
    store.save(state, settings=make_settings())

    raw = (store.sessions_dir / f"{state.session_id}.json").read_text(encoding="utf-8")

    assert "SECRET_API_KEY" not in raw
    assert "api_key" not in raw.lower()
    assert "read_files" not in raw
    assert "inspected_dirs" not in raw


def test_tui_session_load_latest_matches_same_cwd_only(tmp_path: Path) -> None:
    store = make_store(tmp_path)
    settings = make_settings()
    first_cwd = tmp_path / "first"
    second_cwd = tmp_path / "second"
    first_cwd.mkdir()
    second_cwd.mkdir()
    state = store.create(cwd=first_cwd, settings=settings)
    state.messages.append(SessionMessage(role="user", content="You: saved"))
    store.save(state, settings=settings)

    assert store.load_latest(cwd=first_cwd).state is not None
    assert store.load_latest(cwd=second_cwd).state is None


def test_tui_session_loads_legacy_v1_without_provider_messages(tmp_path: Path) -> None:
    store = make_store(tmp_path)
    state = store.create(cwd=tmp_path, settings=make_settings())
    state.messages.append(SessionMessage(role="user", content="You: saved"))
    path = store.save(state, settings=make_settings())
    data = json.loads(path.read_text(encoding="utf-8"))
    data["version"] = 1
    data.pop("provider_messages")
    path.write_text(json.dumps(data), encoding="utf-8")

    result = store.load_latest(cwd=tmp_path)

    assert result.error is None
    assert result.state is not None
    assert result.state.messages == [SessionMessage(role="user", content="You: saved")]
    assert result.state.provider_messages == []
    assert result.state.loaded_skill_ids == []
    assert result.state.todo_items == []


def test_tui_session_loads_legacy_v3_without_todo_items(tmp_path: Path) -> None:
    store = make_store(tmp_path)
    state = store.create(cwd=tmp_path, settings=make_settings())
    path = store.save(state, settings=make_settings())
    data = json.loads(path.read_text(encoding="utf-8"))
    data["version"] = 3
    data.pop("todo_items")
    path.write_text(json.dumps(data), encoding="utf-8")

    result = store.load_latest(cwd=tmp_path)

    assert result.error is None
    assert result.state is not None
    assert result.state.todo_items == []


def test_tui_session_persists_loaded_skill_ids(tmp_path: Path) -> None:
    store = make_store(tmp_path)
    state = store.create(cwd=tmp_path, settings=make_settings())
    state.loaded_skill_ids.extend(["pytest", "reviews"])
    store.save(state, settings=make_settings())

    result = store.load_latest(cwd=tmp_path)

    assert result.error is None
    assert result.state is not None
    assert result.state.loaded_skill_ids == ["pytest", "reviews"]


def test_tui_session_rejects_invalid_provider_messages(tmp_path: Path) -> None:
    store = make_store(tmp_path)
    state = store.create(cwd=tmp_path, settings=make_settings())
    path = store.save(state, settings=make_settings())
    data = json.loads(path.read_text(encoding="utf-8"))
    data["provider_messages"] = [{"role": "bad", "content": "oops"}]
    path.write_text(json.dumps(data), encoding="utf-8")

    result = store.load_latest(cwd=tmp_path)

    assert result.state is None
    assert result.error is not None
    assert "provider message role is invalid" in result.error


def test_tui_session_rejects_invalid_todo_items(tmp_path: Path) -> None:
    store = make_store(tmp_path)
    state = store.create(cwd=tmp_path, settings=make_settings())
    path = store.save(state, settings=make_settings())
    data = json.loads(path.read_text(encoding="utf-8"))
    data["todo_items"] = [{"id": "", "text": "missing id"}]
    path.write_text(json.dumps(data), encoding="utf-8")

    result = store.load_latest(cwd=tmp_path)

    assert result.state is None
    assert result.error is not None
    assert "todo item is invalid" in result.error


@pytest.mark.asyncio
async def test_tui_session_renders_resumed_messages_on_startup(tmp_path: Path) -> None:
    store = make_store(tmp_path)
    state = store.create(cwd=tmp_path, settings=make_settings())
    state.messages.append(SessionMessage(role="user", content="You: earlier"))

    app = CodeGopherApp(
        settings=make_settings(),
        cwd=tmp_path,
        provider_factory=lambda _settings: MockProvider([[{"type": "done"}]]),
        session_store=store,
        session_state=state,
    )

    async with app.run_test() as pilot:
        await pilot.pause()

        assert app.chat_messages == ["You: earlier"]


@pytest.mark.asyncio
async def test_tui_session_resumes_provider_messages_for_next_turn(tmp_path: Path) -> None:
    store = make_store(tmp_path)
    state = store.create(cwd=tmp_path, settings=make_settings())
    state.messages.append(SessionMessage(role="assistant", content="Assistant: earlier"))
    state.provider_messages.extend(
        [
            {"role": "user", "content": "earlier question"},
            {"role": "assistant", "content": "earlier answer"},
        ]
    )
    provider = MockProvider([[{"type": "text_delta", "content": "new answer"}, {"type": "done"}]])
    app = CodeGopherApp(
        settings=make_settings(),
        cwd=tmp_path,
        provider_factory=lambda _settings: provider,
        session_store=store,
        session_state=state,
    )

    async with app.run_test() as pilot:
        await submit(app, pilot, "new question")

        assert provider.calls[0][1:] == [
            {"role": "user", "content": "earlier question"},
            {"role": "assistant", "content": "earlier answer"},
            {"role": "user", "content": "new question"},
        ]


@pytest.mark.asyncio
async def test_tui_session_resumes_todo_items_for_next_turn(tmp_path: Path) -> None:
    store = make_store(tmp_path)
    state = store.create(cwd=tmp_path, settings=make_settings())
    state.todo_items.append(
        TodoItem(
            id="todo-resume",
            text="Resume TODO context",
            status="pending",
        )
    )
    provider = MockProvider([[{"type": "text_delta", "content": "new answer"}, {"type": "done"}]])
    app = CodeGopherApp(
        settings=make_settings(),
        cwd=tmp_path,
        provider_factory=lambda _settings: provider,
        session_store=store,
        session_state=state,
    )

    async with app.run_test() as pilot:
        await submit(app, pilot, "new question")

        assert "Resume TODO context" in str(provider.calls[0][0]["content"])


@pytest.mark.asyncio
async def test_tui_session_resume_uses_same_session_memory(tmp_path: Path) -> None:
    store = make_store(tmp_path)
    settings = make_settings()
    state = store.create(cwd=tmp_path, settings=settings)
    store.save(state, settings=settings)
    memory_store = MemoryStore(data_home=store.data_home)
    kept_entry = memory_store.add_entry(
        "session",
        session_id=state.session_id,
        content="Resume keeps this session memory",
    )
    other_entry = memory_store.add_entry(
        "session",
        session_id="other-session",
        content="Do not show other session memory",
    )
    result = store.load_latest(cwd=tmp_path)
    assert result.error is None
    assert result.state is not None
    app = CodeGopherApp(
        settings=settings,
        cwd=tmp_path,
        provider_factory=lambda _settings: MockProvider([[{"type": "done"}]]),
        session_store=store,
        session_state=result.state,
    )

    async with app.run_test() as pilot:
        await submit(app, pilot, "/memory")

    assert kept_entry.id in app.chat_messages[-1]
    assert "Resume keeps this session memory" in app.chat_messages[-1]
    assert other_entry.id not in app.chat_messages[-1]
    assert "Do not show other session memory" not in app.chat_messages[-1]


@pytest.mark.asyncio
async def test_tui_session_resume_does_not_restore_stale_prior_reads(tmp_path: Path) -> None:
    (tmp_path / "existing.txt").write_text("old", encoding="utf-8")
    store = make_store(tmp_path)
    state = store.create(cwd=tmp_path, settings=make_settings())
    state.provider_messages.extend(
        [
            {"role": "user", "content": "read existing.txt"},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call-old",
                        "type": "function",
                        "function": {
                            "name": "read_file",
                            "arguments": '{"path": "existing.txt"}',
                        },
                    }
                ],
            },
            {"role": "tool", "tool_call_id": "call-old", "content": "old"},
            {"role": "assistant", "content": "read complete"},
        ]
    )
    provider = MockProvider(
        [
            [
                {
                    "type": "tool_call",
                    "tool_call": {
                        "id": "call-new",
                        "name": "write_file",
                        "arguments": {"path": "existing.txt", "content": "new"},
                    },
                },
                {"type": "done"},
            ],
            [{"type": "text_delta", "content": "done"}, {"type": "done"}],
        ]
    )
    app = CodeGopherApp(
        settings=make_settings(),
        cwd=tmp_path,
        provider_factory=lambda _settings: provider,
        session_store=store,
        session_state=state,
    )

    async with app.run_test() as pilot:
        await submit(app, pilot, "write existing.txt")

        assert (tmp_path / "existing.txt").read_text(encoding="utf-8") == "old"
        assert provider.calls[1][-1]["role"] == "tool"
        assert "must read it first" in str(provider.calls[1][-1]["content"])


def test_tui_launcher_auto_resumes_latest_session(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    store = make_store(tmp_path)
    state = store.create(cwd=tmp_path, settings=make_settings())
    state.messages.append(SessionMessage(role="user", content="You: saved"))
    store.save(state, settings=make_settings())
    captured: dict[str, CodeGopherApp] = {}

    def fake_default() -> TuiSessionStore:
        return store

    def fake_run(self: CodeGopherApp) -> None:
        captured["app"] = self

    monkeypatch.setattr(launcher.TuiSessionStore, "default", fake_default)
    monkeypatch.setattr(launcher.CodeGopherApp, "run", fake_run)

    launcher.launch_tui(make_settings(), cwd=tmp_path)

    assert captured["app"].chat_messages == ["You: saved"]


@pytest.mark.asyncio
async def test_tui_session_surfaces_corrupt_session_and_starts_fresh(tmp_path: Path) -> None:
    store = make_store(tmp_path)
    state = store.create(cwd=tmp_path, settings=make_settings())
    path = store.save(state, settings=make_settings())
    path.write_text("{not json", encoding="utf-8")
    result = store.load_latest(cwd=tmp_path)

    app = CodeGopherApp(
        settings=make_settings(),
        cwd=tmp_path,
        provider_factory=lambda _settings: MockProvider([[{"type": "done"}]]),
        session_store=store,
        session_load_error=result.error,
    )

    async with app.run_test() as pilot:
        await pilot.pause()

        assert result.state is None
        assert app.chat_messages[0].startswith("Session resume failed:")


@pytest.mark.asyncio
async def test_tui_clear_does_not_delete_persisted_session_data(tmp_path: Path) -> None:
    store = make_store(tmp_path)
    app = CodeGopherApp(
        settings=make_settings(),
        cwd=tmp_path,
        provider_factory=lambda _settings: MockProvider([[{"type": "done"}]]),
        session_store=store,
    )

    async with app.run_test() as pilot:
        app.append_system_message("Previous message")
        await submit(app, pilot, "/clear")

    assert app.chat_messages == []
    assert app.session_state is not None
    data = read_session_json(store, app.session_state)
    assert data["messages"] == [{"role": "system", "content": "Previous message"}]


class FakeClock:
    def __init__(self, value: datetime) -> None:
        self.value = value

    def __call__(self) -> datetime:
        current = self.value
        self.value = self.value + timedelta(seconds=1)
        return current
