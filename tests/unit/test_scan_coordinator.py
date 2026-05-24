from __future__ import annotations

from codegopher.security.coordinator import build_scan_plan, weakness_hunter_prompt


def test_build_scan_plan_partitions_paths_by_security_role() -> None:
    plan = build_scan_plan(
        [
            "app/routes.py",
            "app/auth/session.py",
            "app/models/user.py",
            "settings.py",
            "workers/jobs.py",
        ]
    )

    by_name = {target.name: target.paths for target in plan.targets}
    assert by_name["routing"] == ["app/routes.py"]
    assert by_name["auth"] == ["app/auth/session.py"]
    assert by_name["data"] == ["app/models/user.py"]
    assert by_name["config"] == ["settings.py"]
    assert by_name["jobs"] == ["workers/jobs.py"]


def test_weakness_hunter_prompt_declares_static_only_contract() -> None:
    target = build_scan_plan(["app/routes.py"]).targets[0]

    prompt = weakness_hunter_prompt(target)

    assert "static-only" in prompt
    assert "Do not run code" in prompt
    assert "app/routes.py" in prompt
