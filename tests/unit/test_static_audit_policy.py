from __future__ import annotations

from pathlib import Path

import pytest

from codegopher.config.schema import ApprovalMode, Settings
from codegopher.core.agent import AgentSession
from codegopher.providers.mock import MockProvider
from codegopher.security.policy import create_static_audit_registry
from codegopher.security.report import DEFAULT_CHAINED_VULNERABILITY_REPORT
from codegopher.tools.base import ToolContext
from codegopher.tools.registry import create_default_registry

VALID_REPORT = """# Chained Vulnerabilities Review

## Candidate Chain Ledger

```json
{"candidate_chains":[{"status":"complete","family":"auth","source":[{"path":"app.py","symbol":"route","line":1}],"hop":[{"path":"app.py","symbol":"check","line":2}],"sink":[{"path":"app.py","symbol":"sink","line":3}],"safe_controls":[{"path":"app.py","symbol":"guard","line":4,"classification":"nearby_only"}],"confidence":"High","missing_evidence":[]}]}
```
"""


def test_static_audit_registry_exposes_only_read_todo_and_report_tools() -> None:
    registry = create_static_audit_registry(create_default_registry())

    assert [tool.name for tool in registry.list()] == [
        "read_file",
        "read_many_files",
        "list_dir",
        "glob_search",
        "grep_search",
        "update_todo",
        "write_chained_vulnerability_report",
    ]


@pytest.mark.asyncio
async def test_chained_audit_policy_denies_shell_even_in_yolo_mode(tmp_path: Path) -> None:
    provider = MockProvider(
        [
            [
                {
                    "type": "tool_call",
                    "tool_call": {
                        "id": "call-shell",
                        "name": "run_shell_command",
                        "arguments": {"command": "echo unsafe"},
                    },
                },
                {"type": "done"},
            ],
            [{"type": "text_delta", "content": "done"}, {"type": "done"}],
        ]
    )
    session = AgentSession(
        provider=provider,
        registry=create_default_registry(),
        settings=Settings(approval_mode=ApprovalMode.yolo),
        cwd=tmp_path,
    )

    result = await session.run_turn("use @skill:chained-vulnerability-static-audit")

    assert result.tool_results[0].is_error is True
    assert "Unknown tool: run_shell_command" in result.tool_results[0].content
    assert "run_shell_command" not in provider.calls[0][0]["content"]


@pytest.mark.asyncio
async def test_chained_audit_policy_allows_only_dedicated_report_writer(
    tmp_path: Path,
) -> None:
    provider = MockProvider(
        [
            [
                {
                    "type": "tool_call",
                    "tool_call": {
                        "id": "call-report",
                        "name": "write_chained_vulnerability_report",
                        "arguments": {"content": VALID_REPORT},
                    },
                },
                {"type": "done"},
            ],
            [{"type": "text_delta", "content": "done"}, {"type": "done"}],
        ]
    )
    session = AgentSession(
        provider=provider,
        registry=create_default_registry(),
        settings=Settings(approval_mode=ApprovalMode.yolo),
        cwd=tmp_path,
    )

    result = await session.run_turn("scan for chained vulnerabilities")

    assert result.tool_results[0].is_error is False
    assert (
        tmp_path / DEFAULT_CHAINED_VULNERABILITY_REPORT
    ).read_text(encoding="utf-8") == VALID_REPORT


@pytest.mark.asyncio
async def test_chained_audit_policy_blocks_hidden_metadata_paths(tmp_path: Path) -> None:
    registry = create_static_audit_registry(create_default_registry())
    tool = registry.get("read_file")
    result = await tool.execute({"path": ".vulns", "_tool_call_id": "call-1"}, ToolContext(cwd=tmp_path))

    assert result.is_error is True
    assert "evaluator metadata" in result.content


@pytest.mark.asyncio
async def test_chained_audit_policy_blocks_answer_key_search_terms(tmp_path: Path) -> None:
    registry = create_static_audit_registry(create_default_registry())
    tool = registry.get("grep_search")

    result = await tool.execute(
        {"query": "OWASP", "_tool_call_id": "call-1"},
        ToolContext(cwd=tmp_path),
    )

    assert result.is_error is True
    assert "answer-key terminology" in result.content


@pytest.mark.asyncio
async def test_chained_audit_policy_blocks_parent_traversal(tmp_path: Path) -> None:
    registry = create_static_audit_registry(create_default_registry())
    tool = registry.get("list_dir")

    result = await tool.execute(
        {"path": "..", "_tool_call_id": "call-1"},
        ToolContext(cwd=tmp_path),
    )

    assert result.is_error is True
    assert "parent-directory traversal" in result.content
