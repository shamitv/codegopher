from __future__ import annotations

from pathlib import Path

import pytest

from codegopher.config.schema import ApprovalMode, Settings
from codegopher.core.agent import AgentSession
from codegopher.providers.mock import MockProvider
from codegopher.security.report import DEFAULT_CHAINED_VULNERABILITY_REPORT
from codegopher.tools.registry import create_default_registry

VALID_CHAINED_REPORT = """# Chained Vulnerabilities Review

## Candidate Chain Ledger

```json
{"candidate_chains":[{"status":"complete","family":"auth","source":[{"path":"app.py","symbol":"route","line":1}],"hop":[{"path":"app.py","symbol":"check","line":2}],"sink":[{"path":"app.py","symbol":"sink","line":3}],"safe_controls":[{"path":"app.py","symbol":"guard","line":4,"classification":"nearby_only"}],"confidence":"High","missing_evidence":[]}]}
```
"""


@pytest.mark.asyncio
async def test_chained_audit_rejects_arbitrary_file_write_and_shell(
    tmp_path: Path,
) -> None:
    provider = MockProvider(
        [
            [
                {
                    "type": "tool_call",
                    "tool_call": {
                        "id": "call-write",
                        "name": "write_file",
                        "arguments": {"path": "pwned.txt", "content": "nope"},
                    },
                },
                {
                    "type": "tool_call",
                    "tool_call": {
                        "id": "call-shell",
                        "name": "run_shell_command",
                        "arguments": {"command": "echo nope"},
                    },
                },
                {
                    "type": "tool_call",
                    "tool_call": {
                        "id": "call-report",
                        "name": "write_chained_vulnerability_report",
                        "arguments": {"content": VALID_CHAINED_REPORT},
                    },
                },
                {"type": "done"},
            ],
            [{"type": "text_delta", "content": "complete"}, {"type": "done"}],
        ]
    )
    session = AgentSession(
        provider=provider,
        registry=create_default_registry(),
        settings=Settings(approval_mode=ApprovalMode.yolo),
        cwd=tmp_path,
    )

    result = await session.run_turn(
        "use @skill:chained-vulnerability-static-audit to audit this fixture"
    )

    assert [tool_result.is_error for tool_result in result.tool_results] == [
        True,
        True,
        False,
    ]
    assert not (tmp_path / "pwned.txt").exists()
    assert (tmp_path / DEFAULT_CHAINED_VULNERABILITY_REPORT).read_text(
        encoding="utf-8"
    ) == VALID_CHAINED_REPORT
