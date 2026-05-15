"""Click entry point for CodeGopher."""

from __future__ import annotations

import click


@click.command()
@click.option("-p", "--prompt", help="Run one headless prompt and exit.")
def app(prompt: str | None) -> None:
    """Run CodeGopher."""
    if prompt:
        click.echo(f"CodeGopher dry run: {prompt}")
        return

    click.echo(
        "CodeGopher v0.1 alpha: pass -p/--prompt to run headless mode. "
        "See docs/product/ROADMAP.md for planned interactive features."
    )
