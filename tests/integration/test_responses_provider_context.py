from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from click.testing import CliRunner

import codegopher.cli.main as cli_main
from codegopher.cli.main import app
from codegopher.config.schema import ApprovalMode, Settings
from codegopher.core.agent import run_agent
from codegopher.providers.openai_responses import OpenAIResponsesProvider
from codegopher.tools.registry import create_default_registry


class AsyncStream:
    def __init__(self, items: list[object] | None = None) -> None:
        self.items = list(items or [])

    def __aiter__(self) -> AsyncStream:
        return self

    async def __anext__(self) -> object:
        if not self.items:
            raise StopAsyncIteration
        return self.items.pop(0)


class FakeResponses:
    def __init__(self, streams: list[AsyncStream]) -> None:
        self.streams = streams
        self.calls: list[dict[str, Any]] = []

    async def create(self, **kwargs):
        self.calls.append(kwargs)
        return self.streams.pop(0)


class FakeClient:
    def __init__(self, streams: list[AsyncStream]) -> None:
        self.responses = FakeResponses(streams)


def make_provider(streams: list[list[object]]) -> tuple[OpenAIResponsesProvider, FakeClient]:
    client = FakeClient([AsyncStream(stream) for stream in streams])
    provider = OpenAIResponsesProvider(
        environ={"OPENAI_API_KEY": "sk-test"},
        client=client,
    )
    return provider, client


async def test_headless_responses_provider_runs_text_turn(tmp_path: Path) -> None:
    provider, client = make_provider(
        [[{"type": "response.output_text.delta", "delta": "hello"}]]
    )

    result = await run_agent(
        prompt="say hello",
        provider=provider,
        registry=create_default_registry(),
        settings=Settings(),
        cwd=tmp_path,
    )

    assert result.final_text == "hello"
    assert client.responses.calls[0]["store"] is False
    assert client.responses.calls[0]["stream"] is True
    assert client.responses.calls[0]["input"][-1] == {"role": "user", "content": "say hello"}


async def test_headless_responses_provider_runs_tool_loop(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("project notes", encoding="utf-8")
    provider, client = make_provider(
        [
            [
                {
                    "type": "response.output_item.done",
                    "item": {
                        "type": "function_call",
                        "id": "fc-1",
                        "call_id": "call-1",
                        "name": "read_file",
                        "arguments": '{"path":"README.md"}',
                    },
                }
            ],
            [{"type": "response.output_text.delta", "delta": "project notes"}],
        ]
    )

    result = await run_agent(
        prompt="read it",
        provider=provider,
        registry=create_default_registry(),
        settings=Settings(approval_mode=ApprovalMode.yolo),
        cwd=tmp_path,
    )

    assert result.final_text == "project notes"
    assert result.tool_results[0].content == "project notes"
    assert client.responses.calls[1]["input"][-1:] == [
        {"type": "function_call_output", "call_id": "call-1", "output": "project notes"},
    ]


def test_cli_responses_provider_json_output(monkeypatch, tmp_path: Path) -> None:
    provider, client = make_provider(
        [[{"type": "response.output_text.delta", "delta": "json answer"}]]
    )
    captured: dict[str, Any] = {}

    def build_provider(settings: Settings) -> OpenAIResponsesProvider:
        captured["api_family"] = settings.providers["openai"][0].api_family.value
        return provider

    monkeypatch.setattr(cli_main, "_build_provider", build_provider)

    with CliRunner().isolated_filesystem(temp_dir=tmp_path):
        result = CliRunner().invoke(
            app,
            ["--no-project-init", "-p", "hello", "--api-family", "responses", "--json"],
        )

    assert result.exit_code == 0
    assert json.loads(result.output)["final_text"] == "json answer"
    assert captured["api_family"] == "responses"
    assert client.responses.calls[0]["store"] is False


def test_cli_responses_provider_debug_output(monkeypatch, tmp_path: Path) -> None:
    provider, _client = make_provider(
        [
            [
                {"type": "response.reasoning_summary_text.delta", "delta": "thinking"},
                {"type": "response.output_text.delta", "delta": "answer"},
            ]
        ]
    )
    monkeypatch.setattr(cli_main, "_build_provider", lambda _settings: provider)

    with CliRunner().isolated_filesystem(temp_dir=tmp_path):
        result = CliRunner().invoke(
            app,
            ["--no-project-init", "-p", "hello", "--api-family", "responses", "--debug"],
        )

    assert result.exit_code == 0
    assert result.output == "Reasoning:\nthinking\nanswer\n"
