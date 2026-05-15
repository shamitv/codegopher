from __future__ import annotations

from dataclasses import dataclass

import pytest

from codegopher.config.schema import ApprovalMode
from codegopher.core.approval import ApprovalRequest, ApprovalResult, should_prompt


@dataclass(frozen=True)
class FakeTool:
    requires_approval: bool


@pytest.mark.parametrize(
    ("mode", "requires_approval", "expected"),
    [
        (ApprovalMode.review, True, True),
        (ApprovalMode.review, False, False),
        (ApprovalMode.auto, True, True),
        (ApprovalMode.auto, False, True),
        (ApprovalMode.yolo, True, False),
        (ApprovalMode.yolo, False, False),
    ],
)
def test_should_prompt(mode: ApprovalMode, requires_approval: bool, expected: bool) -> None:
    assert should_prompt(mode, FakeTool(requires_approval)) is expected


def test_approval_request_and_result_models() -> None:
    request = ApprovalRequest(tool_name="write_file", arguments_preview='{"path":"x"}')
    result = ApprovalResult(approved=False, reason="denied")

    assert request.tool_name == "write_file"
    assert result.reason == "denied"
