"""Slash-command parsing for the interactive TUI."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SlashCommand:
    """Parsed slash command submitted from the prompt input."""

    raw: str
    name: str
    arguments: str


@dataclass(frozen=True)
class SlashCommandDefinition:
    """User-facing slash-command metadata."""

    usage: str
    description: str


COMMAND_DEFINITIONS: tuple[SlashCommandDefinition, ...] = (
    SlashCommandDefinition("/help", "Show available slash commands."),
    SlashCommandDefinition("/clear", "Clear visible chat history."),
    SlashCommandDefinition("/compact [instructions]", "Compact provider context."),
    SlashCommandDefinition("/memory", "List session and project memories."),
    SlashCommandDefinition("/model [NAME]", "Show or update the active model."),
    SlashCommandDefinition("/mode [review|auto|yolo]", "Show or update approval mode."),
    SlashCommandDefinition("/shell COMMAND", "Run a shell command after approval."),
    SlashCommandDefinition("/stats", "Show session counters."),
)


def parse_slash_command(value: str) -> SlashCommand | None:
    """Parse slash-command input, returning None for normal prompts."""
    stripped = value.strip()
    if not stripped.startswith("/"):
        return None

    body = stripped[1:].strip()
    if not body:
        return SlashCommand(raw=stripped, name="", arguments="")

    parts = body.split(maxsplit=1)
    arguments = parts[1].strip() if len(parts) == 2 else ""
    return SlashCommand(raw=stripped, name=parts[0].lower(), arguments=arguments)
