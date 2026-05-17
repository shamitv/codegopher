from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from textual.widgets import Input

from codegopher.config.schema import ApprovalMode, ModelConfig, Settings
from codegopher.providers.mock import MockProvider
from codegopher.tui import CodeGopherApp
from codegopher.tui.session import TuiSessionStore


def make_settings() -> Settings:
    return Settings(model=ModelConfig(provider="openai", name="test-model"))


def make_store(tmp_path: Path) -> TuiSessionStore:
    return TuiSessionStore(data_home=tmp_path / "data")


def make_app(
    tmp_path: Path,
    *,
    settings: Settings | None = None,
    provider: MockProvider | None = None,
) -> CodeGopherApp:
    active_provider = provider or MockProvider([[{"type": "done"}]])
    return CodeGopherApp(
        settings=settings or make_settings(),
        cwd=tmp_path,
        provider_factory=lambda _settings: active_provider,
        session_store=make_store(tmp_path),
    )


async def submit(app: CodeGopherApp, pilot: Any, value: str) -> None:
    input_widget = app.query_one("#prompt-input", Input)
    input_widget.focus()
    input_widget.value = value
    await pilot.press("enter")
    await pilot.pause(0.1)


async def wait_for_turn_to_finish(app: CodeGopherApp, pilot: Any) -> None:
    for _ in range(40):
        if not app.turn_running:
            return
        await pilot.pause(0.05)
    raise AssertionError("agent turn did not finish")


@pytest.mark.asyncio
async def test_memory_command_lists_session_and_project_memories(tmp_path: Path) -> None:
    app = make_app(tmp_path)
    assert app.session_state is not None
    assert app.tool_context.memory_store is not None
    session_entry = app.tool_context.memory_store.add_entry(
        "session",
        session_id=app.session_state.session_id,
        content="Remember the current task",
        source="tool",
    )
    project_entry = app.tool_context.memory_store.add_entry(
        "project",
        cwd=tmp_path,
        content="Project uses pytest",
        source="user",
    )

    async with app.run_test() as pilot:
        await submit(app, pilot, "/memory")

    assert app.chat_messages == [
        "\n".join(
            [
                "Memories:",
                "Session (1):",
                f"- {session_entry.id} [session/tool] Remember the current task",
                "Project (1):",
                f"- {project_entry.id} [project/user] Project uses pytest",
            ]
        )
    ]
    assert app.status_message == "Displayed memory"


@pytest.mark.asyncio
async def test_memory_command_reports_empty_scopes(tmp_path: Path) -> None:
    app = make_app(tmp_path)

    async with app.run_test() as pilot:
        await submit(app, pilot, "/memory")

    assert app.chat_messages == ["Memories:\nSession: none\nProject: none"]
    assert app.status_message == "Displayed memory"


@pytest.mark.asyncio
async def test_memory_command_honors_disabled_memory(tmp_path: Path) -> None:
    settings = make_settings()
    settings.memory.enabled = False
    app = make_app(tmp_path, settings=settings)

    async with app.run_test() as pilot:
        await submit(app, pilot, "/memory")

    assert app.chat_messages == ["Memory is disabled"]


@pytest.mark.asyncio
async def test_memory_command_honors_disabled_scopes(tmp_path: Path) -> None:
    settings = make_settings()
    settings.memory.session_enabled = False
    settings.memory.project_enabled = False
    app = make_app(tmp_path, settings=settings)

    async with app.run_test() as pilot:
        await submit(app, pilot, "/memory")

    assert app.chat_messages == ["Memories:\nSession: disabled\nProject: disabled"]


@pytest.mark.asyncio
async def test_memory_command_rejects_arguments(tmp_path: Path) -> None:
    app = make_app(tmp_path)

    async with app.run_test() as pilot:
        await submit(app, pilot, "/memory extra")

    assert app.chat_messages == ["Error: Usage: /memory"]
    assert app.status_message == "Error: Usage: /memory"


@pytest.mark.asyncio
async def test_forget_command_requires_confirmation(tmp_path: Path) -> None:
    app = make_app(tmp_path)
    assert app.tool_context.memory_store is not None
    entry = app.tool_context.memory_store.add_entry(
        "project",
        cwd=tmp_path,
        content="Forget only after confirmation",
    )

    async with app.run_test() as pilot:
        await submit(app, pilot, f"/forget {entry.id}")

    assert app.tool_context.memory_store.list_entries("project", cwd=tmp_path) == [entry]
    assert app.chat_messages == [
        f"Confirm forget {entry.id}: run /forget {entry.id} --yes"
    ]
    assert app.status_message == "Memory forget needs confirmation"


@pytest.mark.asyncio
async def test_forget_command_deletes_project_memory_with_confirmation(
    tmp_path: Path,
) -> None:
    app = make_app(tmp_path)
    assert app.tool_context.memory_store is not None
    entry = app.tool_context.memory_store.add_entry(
        "project",
        cwd=tmp_path,
        content="Forget this project memory",
    )

    async with app.run_test() as pilot:
        await submit(app, pilot, f"/forget {entry.id} --yes")

    assert app.tool_context.memory_store.list_entries("project", cwd=tmp_path) == []
    assert app.chat_messages == [
        f"Memory deleted: {entry.id} [project/user] Forget this project memory"
    ]
    assert app.status_message == "Memory deleted"


@pytest.mark.asyncio
async def test_forget_command_deletes_session_memory_with_confirmation(
    tmp_path: Path,
) -> None:
    app = make_app(tmp_path)
    assert app.session_state is not None
    assert app.tool_context.memory_store is not None
    entry = app.tool_context.memory_store.add_entry(
        "session",
        session_id=app.session_state.session_id,
        content="Forget this session memory",
    )

    async with app.run_test() as pilot:
        await submit(app, pilot, f"/forget {entry.id} --yes")

    assert (
        app.tool_context.memory_store.list_entries(
            "session",
            session_id=app.session_state.session_id,
        )
        == []
    )
    assert app.chat_messages == [
        f"Memory deleted: {entry.id} [session/user] Forget this session memory"
    ]


@pytest.mark.asyncio
async def test_forget_command_reports_missing_memory(tmp_path: Path) -> None:
    app = make_app(tmp_path)

    async with app.run_test() as pilot:
        await submit(app, pilot, "/forget mem-missing --yes")

    assert app.chat_messages == ["Error: Memory not found: mem-missing"]
    assert app.status_message == "Error: Memory not found: mem-missing"


@pytest.mark.parametrize(
    "command",
    [
        "/forget",
        "/forget mem-1 --no",
        "/forget mem-1 --yes extra",
    ],
)
@pytest.mark.asyncio
async def test_forget_command_rejects_invalid_usage(
    tmp_path: Path,
    command: str,
) -> None:
    app = make_app(tmp_path)

    async with app.run_test() as pilot:
        await submit(app, pilot, command)

    assert app.chat_messages == ["Error: Usage: /forget ID [--yes]"]


@pytest.mark.asyncio
async def test_forget_command_honors_disabled_memory(tmp_path: Path) -> None:
    settings = make_settings()
    settings.memory.enabled = False
    app = make_app(tmp_path, settings=settings)

    async with app.run_test() as pilot:
        await submit(app, pilot, "/forget mem-1 --yes")

    assert app.chat_messages == ["Error: Memory is disabled"]


@pytest.mark.asyncio
async def test_save_memory_tool_renders_memory_event(tmp_path: Path) -> None:
    settings = make_settings()
    settings.approval_mode = ApprovalMode.yolo
    provider = MockProvider(
        [
            [
                {
                    "type": "tool_call",
                    "tool_call": {
                        "id": "call-save",
                        "name": "save_memory",
                        "arguments": {
                            "scope": "project",
                            "content": "Remember visible save events",
                        },
                    },
                },
                {"type": "done"},
            ],
            [{"type": "text_delta", "content": "saved"}, {"type": "done"}],
        ]
    )
    app = make_app(tmp_path, settings=settings, provider=provider)

    async with app.run_test() as pilot:
        await submit(app, pilot, "remember this")
        await wait_for_turn_to_finish(app, pilot)

    assert app.tool_context.memory_store is not None
    entry = app.tool_context.memory_store.list_entries("project", cwd=tmp_path)[0]
    assert f"Memory saved: {entry.id} (project)" in app.chat_messages
    assert "Tool completed: save_memory" not in app.chat_messages


@pytest.mark.asyncio
async def test_failed_save_memory_tool_keeps_visible_error(tmp_path: Path) -> None:
    settings = make_settings()
    settings.approval_mode = ApprovalMode.yolo
    provider = MockProvider(
        [
            [
                {
                    "type": "tool_call",
                    "tool_call": {
                        "id": "call-save",
                        "name": "save_memory",
                        "arguments": {"scope": "global", "content": "bad"},
                    },
                },
                {"type": "done"},
            ],
            [{"type": "text_delta", "content": "saw failure"}, {"type": "done"}],
        ]
    )
    app = make_app(tmp_path, settings=settings, provider=provider)

    async with app.run_test() as pilot:
        await submit(app, pilot, "remember this")
        await wait_for_turn_to_finish(app, pilot)

    assert "Tool failed: save_memory: scope must be 'session' or 'project'" in app.chat_messages
