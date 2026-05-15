"""Click entry point for CodeGopher."""

from __future__ import annotations

import click


@click.command()
def app() -> None:
    """Run CodeGopher."""
    click.echo(
        "CodeGopher v0.1 alpha: pass -p/--prompt to run headless mode. "
        "See docs/product/ROADMAP.md for planned interactive features."
    )
