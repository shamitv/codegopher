from __future__ import annotations

from pathlib import Path

from codegopher.config.schema import ApprovalMode
from codegopher.core.context import build_system_prompt
from codegopher.core.mission import TaskLedger, select_mission_contract
from codegopher.tools.registry import create_default_registry


def test_selects_skill_specific_contract_before_generic_prompt() -> None:
    contract = select_mission_contract(
        prompt="please implement this plan",
        loaded_skill_ids=("chained-vulnerability-static-audit",),
    )

    assert contract is not None
    assert contract.id == "chained-vulnerability-static-audit"
    assert contract.required_tool_calls == ["write_chained_vulnerability_report"]
    contract_text = "\n".join(
        [
            *contract.required_todos,
            *contract.evidence_requirements,
        ]
    ).lower()
    assert "high-risk source families" in contract_text
    assert "discovery is incomplete" in contract_text


def test_simple_prompt_does_not_activate_contract() -> None:
    assert select_mission_contract(prompt="What time is it?", loaded_skill_ids=()) is None


def test_generic_complex_prompt_activates_soft_contract() -> None:
    contract = select_mission_contract(
        prompt="PLEASE IMPLEMENT THIS PLAN: add tests and run verification",
        loaded_skill_ids=(),
    )

    assert contract is not None
    assert contract.id == "generic-complex-task"
    assert contract.required_tool_calls == []


def test_task_ledger_validates_required_tools_and_artifacts(tmp_path: Path) -> None:
    contract = select_mission_contract(
        prompt="scan for chained vulnerabilities",
        loaded_skill_ids=("chained-vulnerability-static-audit",),
    )
    assert contract is not None
    ledger = TaskLedger.start(contract)

    failures = ledger.validate_completion(tmp_path)

    assert "required tool was not called: write_chained_vulnerability_report" in failures
    assert (
        "required artifact is missing: docs/security/CHAINED_VULNERABILITIES_REVIEW.md"
        in failures
    )

    report = tmp_path / "docs/security/CHAINED_VULNERABILITIES_REVIEW.md"
    report.parent.mkdir(parents=True)
    report.write_text(valid_chained_report(), encoding="utf-8")
    ledger.record_tool_call("write_chained_vulnerability_report")

    assert ledger.validate_completion(tmp_path) == []
    assert ledger.observed_artifacts == [
        "docs/security/CHAINED_VULNERABILITIES_REVIEW.md"
    ]


def test_task_ledger_rejects_invalid_chained_report_shape(tmp_path: Path) -> None:
    contract = select_mission_contract(
        prompt="scan for chained vulnerabilities",
        loaded_skill_ids=("chained-vulnerability-static-audit",),
    )
    assert contract is not None
    ledger = TaskLedger.start(contract)
    ledger.record_tool_call("write_chained_vulnerability_report")
    report = tmp_path / "docs/security/CHAINED_VULNERABILITIES_REVIEW.md"
    report.parent.mkdir(parents=True)
    report.write_text("# Report\n", encoding="utf-8")

    failures = ledger.validate_completion(tmp_path)

    assert "report validation failed: missing Candidate Chain Ledger section" in failures
    assert "report validation failed: missing fenced JSON candidate ledger" in failures


def test_system_prompt_includes_mission_contract_context(tmp_path: Path) -> None:
    prompt = build_system_prompt(
        tmp_path,
        create_default_registry(),
        approval_mode=ApprovalMode.yolo,
        mission_items=["Mission: Chained audit", "Required artifacts: report.md"],
    )

    assert "Active mission contract" in prompt
    assert "Mission: Chained audit" in prompt


def valid_chained_report() -> str:
    return """# Chained Vulnerabilities Review

## Candidate Chain Ledger

```json
{
  "candidate_chains": [
    {
      "status": "complete",
      "family": "authorization",
      "source": [{"path": "app.py", "symbol": "create", "line": 10}],
      "hop": [{"path": "app.py", "symbol": "lookup", "line": 20}],
      "sink": [{"path": "app.py", "symbol": "delete", "line": 30}],
      "safe_controls": [
        {
          "path": "app.py",
          "symbol": "require_login",
          "line": 5,
          "classification": "nearby_only"
        }
      ],
      "confidence": "High",
      "missing_evidence": []
    }
  ]
}
```
"""
