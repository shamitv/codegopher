from __future__ import annotations

import json

from click.testing import CliRunner

import codegopher.cli.main as cli_main
from codegopher.cli.main import app
from codegopher.providers.mock import MockProvider


def test_initialized_project_skill_reaches_headless_provider_context(monkeypatch) -> None:
    runner = CliRunner()
    provider = MockProvider([[{"type": "text_delta", "content": "ok"}, {"type": "done"}]])
    monkeypatch.setattr(cli_main, "_build_provider", lambda _settings: provider)

    with runner.isolated_filesystem():
        init_result = runner.invoke(app, ["init"])
        run_result = runner.invoke(app, ["-p", "use @skill:project", "--json"])

    assert init_result.exit_code == 0
    assert run_result.exit_code == 0
    assert json.loads(run_result.output)["final_text"] == "ok"
    system_prompt = str(provider.calls[0][0]["content"])
    assert "Loaded skills" in system_prompt
    assert "Project (project:project)" in system_prompt
    assert "Prefer existing project conventions" in system_prompt


def test_v0_5_builtin_skills_reach_headless_provider_context(monkeypatch) -> None:
    runner = CliRunner()
    provider = MockProvider(
        [
            [{"type": "text_delta", "content": "ok"}, {"type": "done"}],
            [{"type": "text_delta", "content": "ok"}, {"type": "done"}],
            [{"type": "text_delta", "content": "ok"}, {"type": "done"}],
        ]
    )
    monkeypatch.setattr(cli_main, "_build_provider", lambda _settings: provider)

    for skill_id in (
        "repo-domain-docs",
        "repo-tech-docs",
        "crud-owasp-static-audit",
    ):
        result = runner.invoke(app, ["-p", f"use @skill:{skill_id}", "--json"])
        assert result.exit_code == 0
        assert json.loads(result.output)["final_text"] == "ok"

    contexts = [str(call[0]["content"]) for call in provider.calls]
    assert "Repository Domain Documentation (builtin:repo-domain-docs)" in contexts[0]
    assert "docs/domain/" in contexts[0]
    assert "Repository Technical Documentation (builtin:repo-tech-docs)" in contexts[1]
    assert "docs/technical/" in contexts[1]
    assert "CRUD OWASP Static Audit (builtin:crud-owasp-static-audit)" in contexts[2]
    assert "OWASP Top 10:2025" in contexts[2]
