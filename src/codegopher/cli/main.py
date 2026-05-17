"""Click entry point for CodeGopher."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import click

from codegopher.config.loader import CliOverrides, load_settings
from codegopher.config.schema import Settings
from codegopher.core.agent import AgentCallbacks, AgentResult, run_agent
from codegopher.core.errors import AgentLoopError, ConfigurationError, ProviderError
from codegopher.providers.base import Provider
from codegopher.runtime import build_provider
from codegopher.tools.registry import create_default_registry

DEFAULT_PROJECT_SKILL = """# Project

Use this project skill for repository-specific guidance.

- Prefer existing project conventions and nearby patterns.
- Keep changes focused on the user's current request.
- Read relevant files before editing and preserve unrelated work.
- Run the smallest useful verification after changes.
"""


def _build_provider(settings: Settings) -> Provider:
    return build_provider(settings)


def _emit_result(
    result: AgentResult,
    *,
    as_json: bool,
    reasoning_parts: list[str] | None = None,
) -> None:
    if as_json:
        click.echo(json.dumps(result.model_dump(), ensure_ascii=False))
    else:
        if reasoning_parts:
            click.echo("Reasoning:")
            click.echo("".join(reasoning_parts))
        click.echo(result.final_text)


def _streams_are_interactive() -> bool:
    return click.get_text_stream("stdin").isatty() and click.get_text_stream("stdout").isatty()


@click.group(invoke_without_command=True)
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
@click.pass_context
def app(
    ctx: click.Context,
    prompt: str | None,
    model: str | None,
    provider: str | None,
    base_url: str | None,
    approval_mode: str | None,
    debug: bool,
    as_json: bool,
) -> None:
    """Run CodeGopher."""
    if ctx.invoked_subcommand is not None:
        return

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
        reasoning_parts: list[str] = []

        async def on_reasoning_delta(content: str) -> None:
            reasoning_parts.append(content)

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
                    callbacks=AgentCallbacks(on_reasoning_delta=on_reasoning_delta)
                    if debug
                    else None,
                )
            )
        except (ProviderError, AgentLoopError) as exc:
            raise click.ClickException(str(exc)) from exc
        _emit_result(
            result,
            as_json=as_json,
            reasoning_parts=reasoning_parts if debug and not as_json else None,
        )
        return

    if not _streams_are_interactive():
        raise click.ClickException(
            "No prompt provided in non-interactive mode; pass -p/--prompt for headless usage."
        )

    from codegopher.tui import launch_tui

    launch_tui(settings, cwd=Path.cwd())


@app.command("init")
@click.argument(
    "path",
    required=False,
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
)
@click.option("--force", is_flag=True, help="Overwrite the default project skill if it exists.")
def init_project(path: Path | None, *, force: bool) -> None:
    """Create default project-local CodeGopher skill files."""
    target = (path or Path.cwd()).resolve()
    skill_path = target / ".codegopher" / "skills" / "project" / "SKILL.md"
    if skill_path.exists() and not force:
        click.echo(f"Skipped existing {skill_path}")
        return

    skill_path.parent.mkdir(parents=True, exist_ok=True)
    existed = skill_path.exists()
    skill_path.write_text(DEFAULT_PROJECT_SKILL, encoding="utf-8")
    action = "Overwrote" if existed else "Created"
    click.echo(f"{action} {skill_path}")
