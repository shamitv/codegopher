"""Click entry point for CodeGopher."""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

import click

from codegopher.config.loader import CliOverrides, load_settings
from codegopher.config.schema import Settings
from codegopher.core.agent import AgentResult, run_agent
from codegopher.core.errors import AgentLoopError, ConfigurationError, ProviderError
from codegopher.providers.base import Provider
from codegopher.providers.mock import MockProvider
from codegopher.providers.registry import create_provider_registry
from codegopher.tools.registry import create_default_registry


def _build_provider(settings: Settings) -> Provider:
    mock_response = os.environ.get("CODEGOPHER_TEST_MOCK_RESPONSE")
    if mock_response is not None:
        return MockProvider([[{"type": "text_delta", "content": mock_response}, {"type": "done"}]])

    entries = settings.providers.get(settings.model.provider, [])
    selected = next((entry for entry in entries if entry.id == settings.model.name), None)
    if selected is None and entries:
        selected = entries[0]
    base_url = selected.base_url if selected else None
    api_key_env = selected.api_key_env if selected and selected.api_key_env else "OPENAI_API_KEY"
    return create_provider_registry(
        environ=os.environ,
        base_url=base_url,
        api_key_env=api_key_env,
    ).create(settings.model.provider)


def _emit_result(result: AgentResult, *, as_json: bool) -> None:
    if as_json:
        click.echo(json.dumps(result.model_dump(), ensure_ascii=False))
    else:
        click.echo(result.final_text)

@click.command()
@click.option("-p", "--prompt", help="Run one headless prompt and exit.")
@click.option("--model", help="Override the model name.")
@click.option("--provider", help="Override the provider group.")
@click.option("--base-url", help="Override the provider base URL.")
@click.option(
    "--approval-mode",
    type=click.Choice(["review", "auto", "yolo"]),
    help="Choose tool approval behavior.",
)
@click.option("--debug", is_flag=True, help="Include debug diagnostics.")
@click.option("--json", "as_json", is_flag=True, help="Emit machine-readable output.")
def app(
    prompt: str | None,
    model: str | None,
    provider: str | None,
    base_url: str | None,
    approval_mode: str | None,
    debug: bool,
    as_json: bool,
) -> None:
    """Run CodeGopher."""
    try:
        settings = load_settings(
            cli_overrides=CliOverrides(
                model=model,
                provider=provider,
                base_url=base_url,
                approval_mode=approval_mode,
                debug=debug if debug else None,
            )
        )
    except ConfigurationError as exc:
        raise click.ClickException(str(exc)) from exc

    if prompt:
        stdin = click.get_text_stream("stdin")
        full_prompt = prompt
        if not stdin.isatty():
            stdin_text = stdin.read()
            if stdin_text:
                full_prompt = f"{prompt}\n\nInput context:\n{stdin_text}"
        try:
            result = asyncio.run(
                run_agent(
                    prompt=full_prompt,
                    provider=_build_provider(settings),
                    registry=create_default_registry(),
                    settings=settings,
                    cwd=Path.cwd(),
                    stdin_is_tty=stdin.isatty(),
                )
            )
        except (ProviderError, AgentLoopError) as exc:
            raise click.ClickException(str(exc)) from exc
        _emit_result(result, as_json=as_json)
        return

    click.echo(
        "CodeGopher v0.1 alpha: pass -p/--prompt to run headless mode. "
        "See docs/product/ROADMAP.md for planned interactive features."
    )
