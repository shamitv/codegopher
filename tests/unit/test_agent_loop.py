from __future__ import annotations

from pathlib import Path

import pytest

import codegopher.core.agent as agent_module
from codegopher.config.schema import ApprovalMode, ProviderApiFamily, ProviderEntry, Settings
from codegopher.core.agent import AgentCallbacks, AgentResult, run_agent
from codegopher.core.approval import ApprovalRequest, ApprovalResult
from codegopher.core.errors import AgentLoopError, ProviderError
from codegopher.core.types import ToolCall
from codegopher.providers.mock import MockProvider
from codegopher.tools.base import ToolContext, ToolResult
from codegopher.tools.registry import create_default_registry


@pytest.mark.asyncio
async def test_agent_loop_returns_text_only_response(tmp_path: Path) -> None:
    provider = MockProvider([[{"type": "text_delta", "content": "hello"}, {"type": "done"}]])

    result = await run_agent(
        prompt="Say hello",
        provider=provider,
        registry=create_default_registry(),
        settings=Settings(),
        cwd=tmp_path,
    )

    assert result.final_text == "hello"
    assert result.iterations == 1


def test_agent_loop_public_imports_remain_available() -> None:
    assert agent_module.AgentCallbacks is AgentCallbacks
    assert agent_module.AgentResult is AgentResult
    assert agent_module.run_agent is run_agent


@pytest.mark.asyncio
async def test_run_agent_remains_one_shot_without_history_leak(tmp_path: Path) -> None:
    provider = MockProvider(
        [
            [{"type": "text_delta", "content": "first answer"}, {"type": "done"}],
            [{"type": "text_delta", "content": "second answer"}, {"type": "done"}],
        ]
    )

    await run_agent(
        prompt="first question",
        provider=provider,
        registry=create_default_registry(),
        settings=Settings(),
        cwd=tmp_path,
    )
    await run_agent(
        prompt="second question",
        provider=provider,
        registry=create_default_registry(),
        settings=Settings(),
        cwd=tmp_path,
    )

    assert provider.calls[0][1:] == [{"role": "user", "content": "first question"}]
    assert provider.calls[1][1:] == [{"role": "user", "content": "second question"}]


@pytest.mark.asyncio
async def test_agent_loop_emits_text_and_completion_callbacks(tmp_path: Path) -> None:
    provider = MockProvider(
        [[{"type": "text_delta", "content": "hel"}, {"type": "text_delta", "content": "lo"}, {"type": "done"}]]
    )
    text_deltas: list[str] = []
    completed: list[AgentResult] = []

    async def on_text_delta(content: str) -> None:
        text_deltas.append(content)

    async def on_complete(result: AgentResult) -> None:
        completed.append(result)

    result = await run_agent(
        prompt="Say hello",
        provider=provider,
        registry=create_default_registry(),
        settings=Settings(),
        cwd=tmp_path,
        callbacks=AgentCallbacks(on_text_delta=on_text_delta, on_complete=on_complete),
    )

    assert text_deltas == ["hel", "lo"]
    assert completed == [result]


@pytest.mark.asyncio
async def test_agent_loop_emits_reasoning_without_final_text(tmp_path: Path) -> None:
    provider = MockProvider(
        [
            [
                {"type": "reasoning_delta", "content": "thinking"},
                {"type": "text_delta", "content": "answer"},
                {"type": "done"},
            ]
        ]
    )
    reasoning_deltas: list[str] = []

    async def on_reasoning_delta(content: str) -> None:
        reasoning_deltas.append(content)

    result = await run_agent(
        prompt="Think",
        provider=provider,
        registry=create_default_registry(),
        settings=Settings(),
        cwd=tmp_path,
        callbacks=AgentCallbacks(on_reasoning_delta=on_reasoning_delta),
    )

    assert reasoning_deltas == ["thinking"]
    assert result.final_text == "answer"


@pytest.mark.asyncio
async def test_agent_loop_handles_mixed_reasoning_text_and_tool_calls(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("project notes\n", encoding="utf-8")
    provider = MockProvider(
        [
            [
                {"type": "reasoning_delta", "content": "need file"},
                {"type": "text_delta", "content": "checking"},
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
            [{"type": "text_delta", "content": "done"}, {"type": "done"}],
        ]
    )
    reasoning_deltas: list[str] = []
    text_deltas: list[str] = []

    async def on_reasoning_delta(content: str) -> None:
        reasoning_deltas.append(content)

    async def on_text_delta(content: str) -> None:
        text_deltas.append(content)

    result = await run_agent(
        prompt="Inspect",
        provider=provider,
        registry=create_default_registry(),
        settings=Settings(approval_mode=ApprovalMode.yolo),
        cwd=tmp_path,
        callbacks=AgentCallbacks(
            on_reasoning_delta=on_reasoning_delta,
            on_text_delta=on_text_delta,
        ),
    )

    assert reasoning_deltas == ["need file"]
    assert text_deltas == ["checking", "done"]
    assert result.final_text == "done"
    assert result.tool_results[0].content == "project notes"


@pytest.mark.asyncio
async def test_agent_loop_replays_reasoning_content_when_enabled(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("project notes\n", encoding="utf-8")
    provider = MockProvider(
        [
            [
                {"type": "reasoning_delta", "content": "need file"},
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
            [{"type": "text_delta", "content": "done"}, {"type": "done"}],
        ]
    )

    await run_agent(
        prompt="Inspect",
        provider=provider,
        registry=create_default_registry(),
        settings=Settings(
            approval_mode=ApprovalMode.yolo,
            providers={
                "openai": [
                    ProviderEntry(
                        id="gpt-4o",
                        name="GPT-4o",
                        replay_reasoning_content=True,
                    )
                ]
            },
        ),
        cwd=tmp_path,
    )

    assistant_message = provider.calls[1][2]
    assert assistant_message["role"] == "assistant"
    assert assistant_message["reasoning_content"] == "need file"
    assert assistant_message["content"] is None


@pytest.mark.asyncio
async def test_agent_loop_does_not_replay_reasoning_content_for_responses_api(
    tmp_path: Path,
) -> None:
    (tmp_path / "README.md").write_text("project notes\n", encoding="utf-8")
    provider = MockProvider(
        [
            [
                {"type": "reasoning_delta", "content": "need file"},
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
            [{"type": "text_delta", "content": "done"}, {"type": "done"}],
        ]
    )

    await run_agent(
        prompt="Inspect",
        provider=provider,
        registry=create_default_registry(),
        settings=Settings(
            approval_mode=ApprovalMode.yolo,
            providers={
                "openai": [
                    ProviderEntry(
                        id="gpt-4o",
                        name="GPT-4o",
                        api_family=ProviderApiFamily.responses,
                        replay_reasoning_content=True,
                    )
                ]
            },
        ),
        cwd=tmp_path,
    )

    assistant_message = provider.calls[1][2]
    assert "reasoning_content" not in assistant_message


@pytest.mark.asyncio
async def test_agent_loop_does_not_replay_reasoning_content_by_default(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("project notes\n", encoding="utf-8")
    provider = MockProvider(
        [
            [
                {"type": "reasoning_delta", "content": "need file"},
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
            [{"type": "text_delta", "content": "done"}, {"type": "done"}],
        ]
    )

    await run_agent(
        prompt="Inspect",
        provider=provider,
        registry=create_default_registry(),
        settings=Settings(approval_mode=ApprovalMode.yolo),
        cwd=tmp_path,
    )

    assistant_message = provider.calls[1][2]
    assert "reasoning_content" not in assistant_message


@pytest.mark.asyncio
async def test_agent_loop_emits_tool_call_and_result_callbacks(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("project notes\n", encoding="utf-8")
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
            [{"type": "text_delta", "content": "done"}, {"type": "done"}],
        ]
    )
    tool_call_names: list[str] = []
    tool_result_contents: list[str] = []

    async def on_tool_call(tool_call: ToolCall) -> None:
        tool_call_names.append(tool_call["name"])

    async def on_tool_result(tool_result: ToolResult) -> None:
        tool_result_contents.append(tool_result.content)

    await run_agent(
        prompt="Read",
        provider=provider,
        registry=create_default_registry(),
        settings=Settings(),
        cwd=tmp_path,
        callbacks=AgentCallbacks(on_tool_call=on_tool_call, on_tool_result=on_tool_result),
    )

    assert tool_call_names == ["read_file"]
    assert tool_result_contents == ["project notes"]


@pytest.mark.asyncio
async def test_agent_loop_emits_error_callback_for_provider_error_event(tmp_path: Path) -> None:
    provider = MockProvider([[{"type": "error", "message": "provider failed"}]])
    errors: list[str] = []

    async def on_error(message: str) -> None:
        errors.append(message)

    with pytest.raises(ProviderError, match="provider failed"):
        await run_agent(
            prompt="fail",
            provider=provider,
            registry=create_default_registry(),
            settings=Settings(),
            cwd=tmp_path,
            callbacks=AgentCallbacks(on_error=on_error),
        )

    assert errors == ["provider failed"]


@pytest.mark.asyncio
async def test_agent_loop_wraps_callback_failures(tmp_path: Path) -> None:
    provider = MockProvider([[{"type": "text_delta", "content": "hello"}, {"type": "done"}]])

    async def on_text_delta(_content: str) -> None:
        raise RuntimeError("callback boom")

    with pytest.raises(AgentLoopError, match="on_text_delta failed: callback boom"):
        await run_agent(
            prompt="Say hello",
            provider=provider,
            registry=create_default_registry(),
            settings=Settings(),
            cwd=tmp_path,
            callbacks=AgentCallbacks(on_text_delta=on_text_delta),
        )


@pytest.mark.asyncio
async def test_agent_loop_raises_on_max_iterations(tmp_path: Path) -> None:
    provider = MockProvider(
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
    )

    with pytest.raises(AgentLoopError, match="max iterations"):
        await run_agent(
            prompt="Read",
            provider=provider,
            registry=create_default_registry(),
            settings=Settings(),
            cwd=tmp_path,
            max_iterations=1,
        )


@pytest.mark.asyncio
async def test_agent_loop_executes_read_only_tool_call(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("project notes\n", encoding="utf-8")
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
            [{"type": "text_delta", "content": "done"}, {"type": "done"}],
        ]
    )

    result = await run_agent(
        prompt="Read",
        provider=provider,
        registry=create_default_registry(),
        settings=Settings(),
        cwd=tmp_path,
    )

    assert result.final_text == "done"
    assert result.tool_results[0].content == "project notes"


@pytest.mark.asyncio
async def test_agent_loop_uses_provided_tool_context(tmp_path: Path) -> None:
    (tmp_path / "existing.txt").write_text("old", encoding="utf-8")
    tool_context = ToolContext(cwd=tmp_path)
    tool_context.access.record_file_read("existing.txt")
    provider = MockProvider(
        [
            [
                {
                    "type": "tool_call",
                    "tool_call": {
                        "id": "call-1",
                        "name": "write_file",
                        "arguments": {"path": "existing.txt", "content": "new"},
                    },
                },
                {"type": "done"},
            ],
            [{"type": "text_delta", "content": "done"}, {"type": "done"}],
        ]
    )

    result = await run_agent(
        prompt="Write",
        provider=provider,
        registry=create_default_registry(),
        settings=Settings(approval_mode=ApprovalMode.yolo),
        cwd=tmp_path,
        tool_context=tool_context,
    )

    assert result.tool_results[0].is_error is False
    assert (tmp_path / "existing.txt").read_text(encoding="utf-8") == "new"


@pytest.mark.asyncio
async def test_agent_loop_denies_required_tool_when_non_tty(tmp_path: Path) -> None:
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

    result = await run_agent(
        prompt="Write",
        provider=provider,
        registry=create_default_registry(),
        settings=Settings(),
        cwd=tmp_path,
    )

    assert result.tool_results[0].is_error is True
    assert "stdin is not a TTY" in result.tool_results[0].content
    assert not (tmp_path / "new.txt").exists()


@pytest.mark.asyncio
async def test_agent_loop_uses_approval_callback_for_required_tools(tmp_path: Path) -> None:
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
            [{"type": "text_delta", "content": "done"}, {"type": "done"}],
        ]
    )
    approvals: list[ApprovalRequest] = []

    async def on_approval_request(request: ApprovalRequest) -> ApprovalResult:
        approvals.append(request)
        return ApprovalResult(approved=True)

    result = await run_agent(
        prompt="Write",
        provider=provider,
        registry=create_default_registry(),
        settings=Settings(),
        cwd=tmp_path,
        callbacks=AgentCallbacks(on_approval_request=on_approval_request),
    )

    assert len(approvals) == 1
    assert approvals[0].tool_name == "write_file"
    assert '"path": "new.txt"' in approvals[0].arguments_preview
    assert '"content": "hello"' in approvals[0].arguments_preview
    assert "list_dir must inspect parent directory" in result.tool_results[0].content


@pytest.mark.asyncio
async def test_agent_loop_approval_callback_can_deny_tool_execution(tmp_path: Path) -> None:
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

    async def on_approval_request(_request: ApprovalRequest) -> ApprovalResult:
        return ApprovalResult(approved=False, reason="no thanks")

    result = await run_agent(
        prompt="Write",
        provider=provider,
        registry=create_default_registry(),
        settings=Settings(),
        cwd=tmp_path,
        callbacks=AgentCallbacks(on_approval_request=on_approval_request),
    )

    assert result.tool_results[0].is_error is True
    assert result.tool_results[0].content == "no thanks"
    assert not (tmp_path / "new.txt").exists()


@pytest.mark.asyncio
async def test_agent_loop_auto_mode_approval_callback_prompts_for_read_tools(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("project notes\n", encoding="utf-8")
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
            [{"type": "text_delta", "content": "done"}, {"type": "done"}],
        ]
    )
    approvals: list[str] = []

    async def on_approval_request(request: ApprovalRequest) -> ApprovalResult:
        approvals.append(request.tool_name)
        return ApprovalResult(approved=True)

    await run_agent(
        prompt="Read",
        provider=provider,
        registry=create_default_registry(),
        settings=Settings(approval_mode=ApprovalMode.auto),
        cwd=tmp_path,
        callbacks=AgentCallbacks(on_approval_request=on_approval_request),
    )

    assert approvals == ["read_file"]


@pytest.mark.asyncio
async def test_agent_loop_yolo_mode_skips_approval_callback(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("project notes\n", encoding="utf-8")
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
            [{"type": "text_delta", "content": "done"}, {"type": "done"}],
        ]
    )

    async def on_approval_request(_request: ApprovalRequest) -> ApprovalResult:
        raise AssertionError("approval should not be requested")

    await run_agent(
        prompt="Read",
        provider=provider,
        registry=create_default_registry(),
        settings=Settings(approval_mode=ApprovalMode.yolo),
        cwd=tmp_path,
        callbacks=AgentCallbacks(on_approval_request=on_approval_request),
    )


@pytest.mark.asyncio
async def test_agent_loop_wraps_approval_callback_failures(tmp_path: Path) -> None:
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
        ]
    )

    async def on_approval_request(_request: ApprovalRequest) -> ApprovalResult:
        raise RuntimeError("approval exploded")

    with pytest.raises(AgentLoopError, match="on_approval_request failed: approval exploded"):
        await run_agent(
            prompt="Write",
            provider=provider,
            registry=create_default_registry(),
            settings=Settings(),
            cwd=tmp_path,
            callbacks=AgentCallbacks(on_approval_request=on_approval_request),
        )


@pytest.mark.asyncio
async def test_agent_loop_returns_prior_read_rejection(tmp_path: Path) -> None:
    (tmp_path / "existing.txt").write_text("old", encoding="utf-8")
    provider = MockProvider(
        [
            [
                {
                    "type": "tool_call",
                    "tool_call": {
                        "id": "call-1",
                        "name": "write_file",
                        "arguments": {"path": "existing.txt", "content": "new"},
                    },
                },
                {"type": "done"},
            ],
            [{"type": "text_delta", "content": "saw error"}, {"type": "done"}],
        ]
    )

    result = await run_agent(
        prompt="Write",
        provider=provider,
        registry=create_default_registry(),
        settings=Settings(approval_mode=ApprovalMode.yolo),
        cwd=tmp_path,
    )

    assert result.tool_results[0].is_error is True
    assert "must read it first" in result.tool_results[0].content
    assert (tmp_path / "existing.txt").read_text(encoding="utf-8") == "old"


@pytest.mark.asyncio
async def test_agent_loop_writes_after_prior_read(tmp_path: Path) -> None:
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
            [{"type": "text_delta", "content": "updated"}, {"type": "done"}],
        ]
    )

    result = await run_agent(
        prompt="Update",
        provider=provider,
        registry=create_default_registry(),
        settings=Settings(approval_mode=ApprovalMode.yolo),
        cwd=tmp_path,
    )

    assert result.final_text == "updated"
    assert [tool_result.is_error for tool_result in result.tool_results] == [False, False]
    assert (tmp_path / "existing.txt").read_text(encoding="utf-8") == "new"


def test_agent_result_has_structured_cli_shape() -> None:
    result = AgentResult(final_text="done", iterations=1)

    assert result.model_dump() == {
        "final_text": "done",
        "tool_results": [],
        "iterations": 1,
    }


@pytest.mark.asyncio
async def test_chained_audit_contract_recovers_when_report_is_missing(
    tmp_path: Path,
) -> None:
    provider = MockProvider(
        [
            [{"type": "text_delta", "content": "audit complete"}, {"type": "done"}],
            [
                {
                    "type": "tool_call",
                    "tool_call": {
                        "id": "call-report",
                        "name": "write_chained_vulnerability_report",
                        "arguments": {"content": "# Chained report\n"},
                    },
                },
                {"type": "done"},
            ],
            [{"type": "text_delta", "content": "complete"}, {"type": "done"}],
        ]
    )

    result = await run_agent(
        prompt="use @skill:chained-vulnerability-static-audit to audit this repo",
        provider=provider,
        registry=create_default_registry(),
        settings=Settings(approval_mode=ApprovalMode.yolo),
        cwd=tmp_path,
    )

    assert result.final_text == "complete"
    assert result.iterations == 3
    assert "not complete yet" in str(provider.calls[1][-1]["content"])
    assert (
        tmp_path / "docs/security/CHAINED_VULNERABILITIES_REVIEW.md"
    ).read_text(encoding="utf-8") == "# Chained report\n"


@pytest.mark.asyncio
async def test_active_contract_recovers_malformed_tool_call_json(
    tmp_path: Path,
) -> None:
    provider = MockProvider(
        [
            [
                {
                    "type": "error",
                    "message": "Malformed JSON in tool arguments: missing quote",
                }
            ],
            [
                {
                    "type": "tool_call",
                    "tool_call": {
                        "id": "call-report",
                        "name": "write_chained_vulnerability_report",
                        "arguments": {"content": "# Report after repair\n"},
                    },
                },
                {"type": "done"},
            ],
            [{"type": "text_delta", "content": "recovered"}, {"type": "done"}],
        ]
    )

    result = await run_agent(
        prompt="use @skill:chained-vulnerability-static-audit to audit this repo",
        provider=provider,
        registry=create_default_registry(),
        settings=Settings(approval_mode=ApprovalMode.yolo),
        cwd=tmp_path,
    )

    assert result.final_text == "recovered"
    assert "provider returned malformed tool-call JSON" in str(
        provider.calls[1][-1]["content"]
    )
    assert (
        tmp_path / "docs/security/CHAINED_VULNERABILITIES_REVIEW.md"
    ).read_text(encoding="utf-8") == "# Report after repair\n"
