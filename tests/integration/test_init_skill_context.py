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
