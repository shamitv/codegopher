from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from textual.widgets import Input

from codegopher.config.schema import ApprovalMode, ModelConfig, Settings
from codegopher.providers.mock import MockProvider
from codegopher.tui import CodeGopherApp
from codegopher.tui.session import TuiSessionStore


def make_settings() -> Settings:
    return Settings(
        model=ModelConfig(provider="openai", name="test-model"),
        approval_mode=ApprovalMode.yolo,
    )


def write_skill(root: Path, skill_id: str, content: str) -> None:
    path = root / ".codegopher" / "skills" / skill_id / "SKILL.md"
    path.parent.mkdir(parents=True)
    path.write_text(content, encoding="utf-8")


async def submit(app: CodeGopherApp, pilot: Any, value: str) -> None:
    input_widget = app.query_one("#prompt-input", Input)
    input_widget.focus()
    input_widget.value = value
    await pilot.press("enter")
    for _ in range(40):
        if not app.turn_running:
            return
        await pilot.pause(0.05)
    raise AssertionError("turn did not finish")


@pytest.mark.asyncio
async def test_tui_loaded_skill_reaches_provider_context(tmp_path: Path) -> None:
    write_skill(tmp_path, "pytest", "# Pytest\n\nUse pytest from loaded command.")
    provider = MockProvider([[{"type": "text_delta", "content": "ok"}, {"type": "done"}]])
    app = CodeGopherApp(
        settings=make_settings(),
        cwd=tmp_path,
        provider_factory=lambda _settings: provider,
        session_store=TuiSessionStore(data_home=tmp_path / "data"),
    )

    async with app.run_test() as pilot:
        await submit(app, pilot, "/skills load pytest")
        await submit(app, pilot, "hello")

    assert "Use pytest from loaded command." in str(provider.calls[0][0]["content"])


@pytest.mark.asyncio
async def test_tui_skill_mention_reaches_provider_context(tmp_path: Path) -> None:
    write_skill(tmp_path, "reviews", "# Reviews\n\nUse review-specific guidance.")
    provider = MockProvider([[{"type": "text_delta", "content": "ok"}, {"type": "done"}]])
    app = CodeGopherApp(
        settings=make_settings(),
        cwd=tmp_path,
        provider_factory=lambda _settings: provider,
        session_store=TuiSessionStore(data_home=tmp_path / "data"),
    )

    async with app.run_test() as pilot:
        await submit(app, pilot, "please use @skill:reviews")

    assert "Use review-specific guidance." in str(provider.calls[0][0]["content"])
