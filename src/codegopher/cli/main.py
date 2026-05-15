"""Click entry point for CodeGopher."""

from __future__ import annotations

import click

from codegopher.config.loader import CliOverrides, load_settings
from codegopher.core.errors import ConfigurationError

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
def app(
    prompt: str | None,
    model: str | None,
    provider: str | None,
    base_url: str | None,
    approval_mode: str | None,
    debug: bool,
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
        click.echo(f"CodeGopher dry run [{settings.model.provider}/{settings.model.name}]: {prompt}")
        return

    click.echo(
        "CodeGopher v0.1 alpha: pass -p/--prompt to run headless mode. "
        "See docs/product/ROADMAP.md for planned interactive features."
    )
