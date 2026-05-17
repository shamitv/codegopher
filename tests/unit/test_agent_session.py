from __future__ import annotations

from pathlib import Path

import pytest

from codegopher.config.schema import ApprovalMode, ModelConfig, ProviderEntry, Settings
from codegopher.core.agent import AgentCallbacks, AgentResult, AgentSession
from codegopher.core.approval import ApprovalRequest, ApprovalResult
from codegopher.core.conversation import Conversation
from codegopher.core.errors import AgentLoopError, ProviderError
from codegopher.memory import MemoryStore
from codegopher.providers.mock import MockProvider
from codegopher.todo import TodoState
from codegopher.tools.base import ToolContext
from codegopher.tools.registry import create_default_registry


def make_session(
    tmp_path: Path,
    provider: MockProvider,
    *,
    settings: Settings | None = None,
    callbacks: AgentCallbacks | None = None,
    conversation: Conversation | None = None,
    max_iterations: int = 8,
) -> AgentSession:
    return AgentSession(
        provider=provider,
        registry=create_default_registry(),
        settings=settings or Settings(),
        cwd=tmp_path,
        callbacks=callbacks,
        conversation=conversation,
        max_iterations=max_iterations,
    )


def write_skill(root: Path, skill_id: str, content: str) -> None:
    path = root / ".codegopher" / "skills" / skill_id / "SKILL.md"
    path.parent.mkdir(parents=True)
    path.write_text(content, encoding="utf-8")


@pytest.mark.asyncio
async def test_agent_session_preserves_text_conversation_across_turns(tmp_path: Path) -> None:
    provider = MockProvider(
        [
            [{"type": "text_delta", "content": "first answer"}, {"type": "done"}],
            [{"type": "text_delta", "content": "second answer"}, {"type": "done"}],
        ]
    )
    session = make_session(tmp_path, provider)

    first = await session.run_turn("first question")
    second = await session.run_turn("second question")

    assert first.final_text == "first answer"
    assert second.final_text == "second answer"
    assert provider.calls[1][1:] == [
        {"role": "user", "content": "first question"},
        {"role": "assistant", "content": "first answer"},
        {"role": "user", "content": "second question"},
    ]


@pytest.mark.asyncio
async def test_agent_session_preserves_tool_history_across_turns(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("project notes", encoding="utf-8")
    provider = MockProvider(
        [
            [
                {
                    "type": "tool_call",
                    "tool_call": {
                        "id": "call-1",
                        "name": "read_file",
                        "arguments": {"path": "README.md"},
                    },
                },
                {"type": "done"},
            ],
            [{"type": "text_delta", "content": "read complete"}, {"type": "done"}],
            [{"type": "text_delta", "content": "next"}, {"type": "done"}],
        ]
    )
    session = make_session(tmp_path, provider, settings=Settings(approval_mode=ApprovalMode.yolo))

    await session.run_turn("read the file")
    await session.run_turn("what did you read?")

    messages = provider.calls[2][1:]
    assert messages[0] == {"role": "user", "content": "read the file"}
    assert messages[1]["role"] == "assistant"
    assert messages[1]["tool_calls"][0]["function"]["name"] == "read_file"
    assert messages[2] == {
        "role": "tool",
        "tool_call_id": "call-1",
        "content": "project notes",
    }
    assert messages[3] == {"role": "assistant", "content": "read complete"}
    assert messages[4] == {"role": "user", "content": "what did you read?"}


@pytest.mark.asyncio
async def test_agent_session_callbacks_and_reasoning_match_agent_loop(tmp_path: Path) -> None:
    provider = MockProvider(
        [
            [
                {"type": "reasoning_delta", "content": "thinking"},
                {"type": "text_delta", "content": "answer"},
                {"type": "done"},
            ]
        ]
    )
    reasoning: list[str] = []
    text: list[str] = []
    completed: list[AgentResult] = []

    async def on_reasoning_delta(content: str) -> None:
        reasoning.append(content)

    async def on_text_delta(content: str) -> None:
        text.append(content)

    async def on_complete(result: AgentResult) -> None:
        completed.append(result)

    session = make_session(
        tmp_path,
        provider,
        callbacks=AgentCallbacks(
            on_reasoning_delta=on_reasoning_delta,
            on_text_delta=on_text_delta,
            on_complete=on_complete,
        ),
    )

    result = await session.run_turn("think")

    assert reasoning == ["thinking"]
    assert text == ["answer"]
    assert completed == [result]


@pytest.mark.asyncio
async def test_agent_session_approval_callback_can_deny_tool_execution(tmp_path: Path) -> None:
    provider = MockProvider(
        [
            [
                {
                    "type": "tool_call",
                    "tool_call": {
                        "id": "call-1",
                        "name": "write_file",
                        "arguments": {"path": "new.txt", "content": "hello"},
                    },
                },
                {"type": "done"},
            ],
            [{"type": "text_delta", "content": "denied"}, {"type": "done"}],
        ]
    )
    approvals: list[ApprovalRequest] = []

    async def on_approval_request(request: ApprovalRequest) -> ApprovalResult:
        approvals.append(request)
        return ApprovalResult(approved=False, reason="not safe")

    session = make_session(
        tmp_path,
        provider,
        callbacks=AgentCallbacks(on_approval_request=on_approval_request),
    )

    result = await session.run_turn("write")

    assert approvals[0].tool_name == "write_file"
    assert result.tool_results[0].content == "not safe"
    assert result.tool_results[0].is_error is True
    assert not (tmp_path / "new.txt").exists()


@pytest.mark.asyncio
async def test_agent_session_surfaces_provider_errors(tmp_path: Path) -> None:
    errors: list[str] = []

    async def on_error(message: str) -> None:
        errors.append(message)

    session = make_session(
        tmp_path,
        MockProvider([[{"type": "error", "message": "provider failed"}]]),
        callbacks=AgentCallbacks(on_error=on_error),
    )

    with pytest.raises(ProviderError, match="provider failed"):
        await session.run_turn("fail")

    assert errors == ["provider failed"]


@pytest.mark.asyncio
async def test_agent_session_raises_on_max_iterations(tmp_path: Path) -> None:
    session = make_session(
        tmp_path,
        MockProvider(
            [
                [
                    {
                        "type": "tool_call",
                        "tool_call": {
                            "id": "call-1",
                            "name": "read_file",
                            "arguments": {"path": "missing.txt"},
                        },
                    },
                    {"type": "done"},
                ]
            ]
        ),
        max_iterations=1,
    )

    with pytest.raises(AgentLoopError, match="max iterations"):
        await session.run_turn("read")


@pytest.mark.asyncio
async def test_agent_session_respects_supplied_initial_conversation(tmp_path: Path) -> None:
    conversation = Conversation()
    conversation.append_user("earlier")
    conversation.append_assistant("saved answer")
    provider = MockProvider([[{"type": "text_delta", "content": "new answer"}, {"type": "done"}]])
    session = make_session(tmp_path, provider, conversation=conversation)

    await session.run_turn("new question")

    assert provider.calls[0][1:] == [
        {"role": "user", "content": "earlier"},
        {"role": "assistant", "content": "saved answer"},
        {"role": "user", "content": "new question"},
    ]


@pytest.mark.asyncio
async def test_agent_session_feeds_active_todo_state_into_provider_context(
    tmp_path: Path,
) -> None:
    provider = MockProvider([[{"type": "text_delta", "content": "done"}, {"type": "done"}]])
    todo_state = TodoState()
    active = todo_state.add("Keep provider context fresh", source="user")
    completed = todo_state.add("Old item", source="user")
    todo_state.done(completed.id)
    session = AgentSession(
        provider=provider,
        registry=create_default_registry(),
        settings=Settings(),
        cwd=tmp_path,
        tool_context=ToolContext(cwd=tmp_path, todo_state=todo_state),
    )

    await session.run_turn("continue")

    system_prompt = str(provider.calls[0][0]["content"])
    assert "Active TODOs" in system_prompt
    assert f"[{active.id}] pending: Keep provider context fresh" in system_prompt
    assert "Old item" not in system_prompt


@pytest.mark.asyncio
async def test_agent_session_update_todo_tool_reaches_next_provider_context(
    tmp_path: Path,
) -> None:
    provider = MockProvider(
        [
            [
                {
                    "type": "tool_call",
                    "tool_call": {
                        "id": "call-1",
                        "name": "update_todo",
                        "arguments": {"action": "add", "text": "Review prompt wiring"},
                    },
                },
                {"type": "done"},
            ],
            [{"type": "text_delta", "content": "tracked"}, {"type": "done"}],
        ]
    )
    session = make_session(tmp_path, provider)

    result = await session.run_turn("track this")

    assert result.final_text == "tracked"
    system_prompt = str(provider.calls[1][0]["content"])
    assert "Active TODOs" in system_prompt
    assert "pending: Review prompt wiring" in system_prompt


@pytest.mark.asyncio
async def test_agent_session_manual_compaction_replaces_older_history(
    tmp_path: Path,
) -> None:
    conversation = Conversation()
    for index in range(1, 4):
        conversation.append_user(f"question {index}")
        conversation.append_assistant(f"answer {index}")
    provider = MockProvider(
        [[{"type": "text_delta", "content": "summary text"}, {"type": "done"}]]
    )
    session = make_session(tmp_path, provider, conversation=conversation)

    entry = await session.compact(instructions="keep decisions")

    assert entry.reason == "manual"
    assert entry.summary == "summary text"
    assert provider.calls[0][0]["role"] == "system"
    assert "keep decisions" in str(provider.calls[0][1]["content"])
    assert session.conversation.messages[0]["role"] == "system"
    assert "summary text" in str(session.conversation.messages[0]["content"])
    assert {"role": "user", "content": "question 1"} not in session.conversation.messages
    assert {"role": "user", "content": "question 2"} in session.conversation.messages


@pytest.mark.asyncio
async def test_agent_session_automatically_compacts_before_threshold_turn(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from codegopher.core import context_budget

    monkeypatch.setattr(context_budget, "tiktoken", None)
    conversation = Conversation()
    for index in range(1, 4):
        conversation.append_user(f"question {index} with enough text")
        conversation.append_assistant(f"answer {index} with enough text")
    provider = MockProvider(
        [
            [{"type": "text_delta", "content": "automatic summary"}, {"type": "done"}],
            [{"type": "text_delta", "content": "new answer"}, {"type": "done"}],
        ]
    )
    settings = Settings(
        model=ModelConfig(provider="openai", name="small"),
        providers={"openai": [ProviderEntry(id="small", name="Small", context_window=40)]},
    )
    compacted = []

    async def on_compaction(entry) -> None:
        compacted.append(entry)

    session = make_session(
        tmp_path,
        provider,
        settings=settings,
        conversation=conversation,
        callbacks=AgentCallbacks(on_compaction=on_compaction),
    )
    assert session.tool_context.todo_state is not None
    automatic_todo = session.tool_context.todo_state.add("Keep automatic TODO")
    finished_todo = session.tool_context.todo_state.add("Finished automatic TODO")
    session.tool_context.todo_state.done(finished_todo.id)

    result = await session.run_turn("new question with enough text")

    assert result.final_text == "new answer"
    assert compacted[0].reason == "automatic"
    assert provider.calls[0][0]["role"] == "system"
    compaction_prompt = str(provider.calls[0][1]["content"])
    assert f"[{automatic_todo.id}] pending: Keep automatic TODO" in compaction_prompt
    assert "Finished automatic TODO" not in compaction_prompt
    assert provider.calls[1][1]["role"] == "system"
    assert "automatic summary" in str(provider.calls[1][1]["content"])
    assert {"role": "user", "content": "question 1 with enough text"} not in (
        session.conversation.messages
    )


@pytest.mark.asyncio
async def test_agent_session_compaction_includes_extra_context(
    tmp_path: Path,
) -> None:
    conversation = Conversation()
    conversation.append_user("first")
    conversation.append_assistant("answer")
    conversation.append_user("second")
    provider = MockProvider(
        [[{"type": "text_delta", "content": "summary text"}, {"type": "done"}]]
    )
    session = AgentSession(
        provider=provider,
        registry=create_default_registry(),
        settings=Settings(),
        cwd=tmp_path,
        conversation=conversation,
        memory_context=["Project memory"],
        skill_context=["Skill context"],
        todo_context=["TODO context"],
    )

    await session.compact()

    prompt = str(provider.calls[0][1]["content"])
    assert "Project memory" in prompt
    assert "Skill context" in prompt
    assert "TODO context" in prompt


@pytest.mark.asyncio
async def test_agent_session_compaction_uses_active_todo_state_from_tool_context(
    tmp_path: Path,
) -> None:
    conversation = Conversation()
    conversation.append_user("first")
    conversation.append_assistant("answer")
    conversation.append_user("second")
    provider = MockProvider(
        [[{"type": "text_delta", "content": "summary text"}, {"type": "done"}]]
    )
    todo_state = TodoState()
    active = todo_state.add("Include in compaction", source="user")
    completed = todo_state.add("Exclude from compaction", source="user")
    todo_state.done(completed.id)
    session = AgentSession(
        provider=provider,
        registry=create_default_registry(),
        settings=Settings(),
        cwd=tmp_path,
        conversation=conversation,
        tool_context=ToolContext(cwd=tmp_path, todo_state=todo_state),
    )

    await session.compact()

    prompt = str(provider.calls[0][1]["content"])
    assert f"[{active.id}] pending: Include in compaction" in prompt
    assert "Exclude from compaction" not in prompt


@pytest.mark.asyncio
async def test_agent_session_compaction_failure_preserves_conversation(
    tmp_path: Path,
) -> None:
    conversation = Conversation()
    conversation.append_user("first")
    conversation.append_assistant("answer")
    original = conversation.provider_messages()
    session = make_session(
        tmp_path,
        MockProvider([[{"type": "error", "message": "provider failed"}]]),
        conversation=conversation,
    )

    with pytest.raises(ProviderError, match="provider failed"):
        await session.compact()

    assert session.conversation.messages == original


@pytest.mark.asyncio
async def test_agent_session_feeds_selected_memories_into_provider_context(
    tmp_path: Path,
) -> None:
    store = MemoryStore(data_home=tmp_path / "data")
    store.add_entry("project", cwd=tmp_path, content="Project uses pytest")
    store.add_entry(
        "session",
        session_id="session-1",
        content="Current task is memory tests",
    )
    provider = MockProvider([[{"type": "text_delta", "content": "ok"}, {"type": "done"}]])
    session = AgentSession(
        provider=provider,
        registry=create_default_registry(),
        settings=Settings(),
        cwd=tmp_path,
        tool_context=ToolContext(
            cwd=tmp_path,
            memory_store=store,
            session_id="session-1",
        ),
    )

    await session.run_turn("hello")

    system_prompt = str(provider.calls[0][0]["content"])
    assert "Selected memories" in system_prompt
    assert "Project uses pytest" in system_prompt
    assert "Current task is memory tests" in system_prompt


@pytest.mark.asyncio
async def test_agent_session_loads_explicit_skill_into_provider_context(
    tmp_path: Path,
) -> None:
    write_skill(
        tmp_path,
        "pytest",
        """---
name: Pytest
keywords: pytest
---
Prefer focused pytest commands.
""",
    )
    provider = MockProvider([[{"type": "text_delta", "content": "ok"}, {"type": "done"}]])
    session = make_session(tmp_path, provider)

    await session.run_turn("use @skill:pytest for this")

    system_prompt = str(provider.calls[0][0]["content"])
    assert "Loaded skills" in system_prompt
    assert "Pytest (project:pytest)" in system_prompt
    assert "Prefer focused pytest commands." in system_prompt
    assert session.skill_manager.loaded_ids == ("pytest",)


@pytest.mark.asyncio
async def test_agent_session_autoloads_keyword_skill_into_provider_context(
    tmp_path: Path,
) -> None:
    write_skill(
        tmp_path,
        "reviews",
        """---
name: Reviews
keywords: review
---
Review diffs for regressions.
""",
    )
    provider = MockProvider([[{"type": "text_delta", "content": "ok"}, {"type": "done"}]])
    session = make_session(tmp_path, provider)

    await session.run_turn("please review this change")

    system_prompt = str(provider.calls[0][0]["content"])
    assert "Review diffs for regressions." in system_prompt
    assert session.skill_manager.loaded_ids == ("reviews",)


@pytest.mark.asyncio
async def test_save_memory_tool_result_reaches_next_provider_context(
    tmp_path: Path,
) -> None:
    store = MemoryStore(data_home=tmp_path / "data")
    provider = MockProvider(
        [
            [
                {
                    "type": "tool_call",
                    "tool_call": {
                        "id": "call-1",
                        "name": "save_memory",
                        "arguments": {"scope": "project", "content": "Remember pytest"},
                    },
                },
                {"type": "done"},
            ],
            [{"type": "text_delta", "content": "saved"}, {"type": "done"}],
        ]
    )
    session = AgentSession(
        provider=provider,
        registry=create_default_registry(),
        settings=Settings(approval_mode=ApprovalMode.yolo),
        cwd=tmp_path,
        tool_context=ToolContext(cwd=tmp_path, memory_store=store),
    )

    await session.run_turn("save this")

    assert store.list_entries("project", cwd=tmp_path)[0].content == "Remember pytest"
    assert "Remember pytest" in str(provider.calls[1][0]["content"])


@pytest.mark.asyncio
async def test_agent_session_tool_context_persists_across_turns(tmp_path: Path) -> None:
    (tmp_path / "existing.txt").write_text("old", encoding="utf-8")
    provider = MockProvider(
        [
            [
                {
                    "type": "tool_call",
                    "tool_call": {
                        "id": "call-1",
                        "name": "read_file",
                        "arguments": {"path": "existing.txt"},
                    },
                },
                {"type": "done"},
            ],
            [{"type": "text_delta", "content": "read"}, {"type": "done"}],
            [
                {
                    "type": "tool_call",
                    "tool_call": {
                        "id": "call-2",
                        "name": "write_file",
                        "arguments": {"path": "existing.txt", "content": "new"},
                    },
                },
                {"type": "done"},
            ],
            [{"type": "text_delta", "content": "written"}, {"type": "done"}],
        ]
    )
    session = make_session(tmp_path, provider, settings=Settings(approval_mode=ApprovalMode.yolo))

    await session.run_turn("read")
    await session.run_turn("write")

    assert (tmp_path / "existing.txt").read_text(encoding="utf-8") == "new"


@pytest.mark.asyncio
async def test_agent_session_directory_inspection_persists_across_turns(tmp_path: Path) -> None:
    provider = MockProvider(
        [
            [
                {
                    "type": "tool_call",
                    "tool_call": {
                        "id": "call-1",
                        "name": "list_dir",
                        "arguments": {"path": "."},
                    },
                },
                {"type": "done"},
            ],
            [{"type": "text_delta", "content": "listed"}, {"type": "done"}],
            [
                {
                    "type": "tool_call",
                    "tool_call": {
                        "id": "call-2",
                        "name": "write_file",
                        "arguments": {"path": "created.txt", "content": "new"},
                    },
                },
                {"type": "done"},
            ],
            [{"type": "text_delta", "content": "created"}, {"type": "done"}],
        ]
    )
    session = make_session(tmp_path, provider, settings=Settings(approval_mode=ApprovalMode.yolo))

    await session.run_turn("list")
    await session.run_turn("create")

    assert (tmp_path / "created.txt").read_text(encoding="utf-8") == "new"


@pytest.mark.asyncio
async def test_agent_sessions_do_not_share_conversation_or_tool_access(tmp_path: Path) -> None:
    (tmp_path / "existing.txt").write_text("old", encoding="utf-8")
    first_provider = MockProvider(
        [
            [
                {
                    "type": "tool_call",
                    "tool_call": {
                        "id": "call-1",
                        "name": "read_file",
                        "arguments": {"path": "existing.txt"},
                    },
                },
                {"type": "done"},
            ],
            [{"type": "text_delta", "content": "read"}, {"type": "done"}],
        ]
    )
    second_provider = MockProvider(
        [
            [
                {
                    "type": "tool_call",
                    "tool_call": {
                        "id": "call-2",
                        "name": "write_file",
                        "arguments": {"path": "existing.txt", "content": "new"},
                    },
                },
                {"type": "done"},
            ],
            [{"type": "text_delta", "content": "done"}, {"type": "done"}],
        ]
    )
    settings = Settings(approval_mode=ApprovalMode.yolo)
    first = make_session(tmp_path, first_provider, settings=settings)
    second = make_session(tmp_path, second_provider, settings=settings)

    await first.run_turn("read")
    result = await second.run_turn("write")

    assert result.tool_results[0].is_error is True
    assert "must read it first" in result.tool_results[0].content
    assert second_provider.calls[0][1:] == [{"role": "user", "content": "write"}]
    assert (tmp_path / "existing.txt").read_text(encoding="utf-8") == "old"
