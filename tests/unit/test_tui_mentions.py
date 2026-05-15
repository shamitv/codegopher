from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

import pytest
from textual.widgets import Input

from codegopher.config.schema import ApprovalMode, ModelConfig, Settings
from codegopher.core.types import Message, StreamEvent, ToolSchema
from codegopher.providers.base import ProviderCapabilities
from codegopher.providers.mock import MockProvider
from codegopher.tools.base import ToolContext
from codegopher.tui import CodeGopherApp
from codegopher.tui.mentions import MentionToken, expand_mentions, parse_mentions


def make_settings() -> Settings:
    return Settings(
        model=ModelConfig(provider="openai", name="test-model"),
        approval_mode=ApprovalMode.yolo,
    )


def make_app(tmp_path: Path, provider: Any) -> CodeGopherApp:
    return CodeGopherApp(
        settings=make_settings(),
        cwd=tmp_path,
        provider_factory=lambda _settings: provider,
    )


async def submit(app: CodeGopherApp, pilot: Any, value: str, *, pause: float = 0.1) -> None:
    input_widget = app.query_one("#prompt-input", Input)
    input_widget.focus()
    input_widget.value = value
    await pilot.press("enter")
    await pilot.pause(pause)


def test_parse_mentions_handles_paths_and_globs() -> None:
    assert parse_mentions("check @README.md and @src/**/*.py @glob:tests/*.py") == (
        MentionToken(raw="@README.md", value="README.md", kind="path"),
        MentionToken(raw="@src/**/*.py", value="src/**/*.py", kind="glob"),
        MentionToken(raw="@glob:tests/*.py", value="tests/*.py", kind="glob"),
    )


def test_expand_literal_path_relative_to_cwd_and_marks_prior_read(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("project notes\n", encoding="utf-8")
    context = ToolContext(cwd=tmp_path)

    expansion = expand_mentions(
        "explain @README.md",
        cwd=tmp_path,
        tool_context=context,
    )

    assert expansion.errors == ()
    assert expansion.files[0].path == "README.md"
    assert "Mentioned files:" in expansion.prompt
    assert "project notes" in expansion.prompt
    assert context.access.has_read_file("README.md")


def test_expand_glob_mentions_respect_ignore_file(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "visible.py").write_text("print('visible')", encoding="utf-8")
    (tmp_path / "src" / "ignored.py").write_text("print('ignored')", encoding="utf-8")
    (tmp_path / ".codegopherignore").write_text("ignored.py\n", encoding="utf-8")

    expansion = expand_mentions(
        "summarize @src/*.py",
        cwd=tmp_path,
        tool_context=ToolContext(cwd=tmp_path),
    )

    assert expansion.errors == ()
    assert [file.path for file in expansion.files] == ["src/visible.py"]
    assert "visible" in expansion.prompt
    assert "ignored" not in expansion.prompt


@pytest.mark.parametrize(
    ("prompt", "expected"),
    [
        ("read @missing.txt", "file not found"),
        ("read @.", "not a file"),
        ("read @../outside.txt", "outside project directory"),
    ],
)
def test_expand_literal_mentions_surface_failures(
    tmp_path: Path,
    prompt: str,
    expected: str,
) -> None:
    (tmp_path.parent / "outside.txt").write_text("outside", encoding="utf-8")

    expansion = expand_mentions(prompt, cwd=tmp_path, tool_context=ToolContext(cwd=tmp_path))

    assert expected in expansion.errors[0]


def test_expand_mentions_surfaces_binary_file_failure(tmp_path: Path) -> None:
    (tmp_path / "image.bin").write_bytes(b"\xff\xfe\x00")

    expansion = expand_mentions(
        "read @image.bin",
        cwd=tmp_path,
        tool_context=ToolContext(cwd=tmp_path),
    )

    assert "not a UTF-8 text file" in expansion.errors[0]


def test_expand_mentions_surfaces_ignored_literal_failure(tmp_path: Path) -> None:
    (tmp_path / "secret.txt").write_text("secret", encoding="utf-8")
    (tmp_path / ".codegopherignore").write_text("secret.txt\n", encoding="utf-8")

    expansion = expand_mentions(
        "read @secret.txt",
        cwd=tmp_path,
        tool_context=ToolContext(cwd=tmp_path),
    )

    assert "ignored by .codegopherignore" in expansion.errors[0]


@pytest.mark.asyncio
async def test_tui_expands_mentions_before_provider_submission(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("project notes\n", encoding="utf-8")
    provider = RecordingProvider()
    app = make_app(tmp_path, provider)

    async with app.run_test() as pilot:
        await submit(app, pilot, "explain @README.md")

        assert app.chat_messages[0] == "You: explain @README.md"
        assert app.chat_messages[1] == "Expanded 1 file mention(s): README.md"
        assert provider.prompts
        assert "Mentioned files:" in provider.prompts[0]
        assert "project notes" in provider.prompts[0]


@pytest.mark.asyncio
async def test_tui_failed_mention_does_not_call_provider(tmp_path: Path) -> None:
    provider = MockProvider([[{"type": "text_delta", "content": "unused"}, {"type": "done"}]])
    app = make_app(tmp_path, provider)

    async with app.run_test() as pilot:
        await submit(app, pilot, "explain @missing.md")

        assert len(provider.calls) == 0
        assert app.chat_messages[1].startswith("Mention expansion failed:")
        assert "file not found" in app.chat_messages[1]


@pytest.mark.asyncio
async def test_tui_mention_expansion_marks_prior_reads(tmp_path: Path) -> None:
    (tmp_path / "existing.txt").write_text("old", encoding="utf-8")
    provider = MockProvider([[{"type": "text_delta", "content": "ok"}, {"type": "done"}]])
    app = make_app(tmp_path, provider)

    async with app.run_test() as pilot:
        await submit(app, pilot, "remember @existing.txt")

        assert app.tool_context.access.has_read_file("existing.txt")


class RecordingProvider:
    capabilities = ProviderCapabilities(streaming=True, tool_calls=True)

    def __init__(self) -> None:
        self.prompts: list[str] = []

    async def stream(
        self,
        messages: list[Message],
        tools: list[ToolSchema],
        *,
        model: str,
        temperature: float,
        max_output_tokens: int,
    ) -> AsyncIterator[StreamEvent]:
        self.prompts.append(str(messages[-1]["content"]))
        yield {"type": "text_delta", "content": "ok"}
        yield {"type": "done"}
