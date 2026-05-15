from __future__ import annotations

from pathlib import Path

import pytest

from codegopher.config.schema import ApprovalMode, Settings
from codegopher.core.agent import run_agent
from codegopher.core.errors import AgentLoopError
from codegopher.providers.mock import MockProvider
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
