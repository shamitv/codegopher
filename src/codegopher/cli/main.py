"""Click entry point for CodeGopher."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import click

from codegopher.config.loader import CliOverrides, load_settings
from codegopher.config.schema import Settings
from codegopher.core.agent import AgentResult, run_agent
from codegopher.core.errors import AgentLoopError, ConfigurationError, ProviderError
from codegopher.providers.base import Provider
from codegopher.runtime import build_provider
from codegopher.tools.registry import create_default_registry


def _build_provider(settings: Settings) -> Provider:
    return build_provider(settings)


def _emit_result(result: AgentResult, *, as_json: bool) -> None:
    if as_json:
        click.echo(json.dumps(result.model_dump(), ensure_ascii=False))
    else:
        click.echo(result.final_text)


def _streams_are_interactive() -> bool:
    return click.get_text_stream("stdin").isatty() and click.get_text_stream("stdout").isatty()


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

    if not _streams_are_interactive():
        raise click.ClickException(
            "No prompt provided in non-interactive mode; pass -p/--prompt for headless usage."
        )

    from codegopher.tui import launch_tui

    launch_tui(settings, cwd=Path.cwd())
