from __future__ import annotations

from pathlib import Path

import pytest

from codegopher.config.schema import ApprovalMode, Settings
from codegopher.core.agent import AgentCallbacks, AgentResult, AgentSession
from codegopher.core.approval import ApprovalRequest, ApprovalResult
from codegopher.core.conversation import Conversation
from codegopher.core.errors import AgentLoopError, ProviderError
from codegopher.providers.mock import MockProvider
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
