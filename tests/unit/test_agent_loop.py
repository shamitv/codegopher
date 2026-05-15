from __future__ import annotations

from pathlib import Path

import pytest

from codegopher.config.schema import Settings
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
