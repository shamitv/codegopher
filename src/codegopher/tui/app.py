"""Textual application shell for interactive CodeGopher sessions."""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from textual.app import App, ComposeResult
from textual.binding import BindingType
from textual.containers import Vertical
from textual.widgets import Footer, Header, Input, RichLog, Static

from codegopher.config.schema import Settings


class CodeGopherApp(App[None]):
    """Minimal interactive shell for v0.2."""

    CSS = """
    Screen {
        layout: vertical;
    }

    #session-status {
        height: 3;
        padding: 0 1;
        border-bottom: solid $primary;
    }

    #chat-history {
        height: 1fr;
        padding: 1;
    }

    #prompt-input {
        dock: bottom;
    }
    """
    BINDINGS: ClassVar[list[BindingType]] = [
        ("ctrl+q", "quit", "Quit"),
        ("ctrl+i", "focus_input", "Focus input"),
    ]

    def __init__(self, *, settings: Settings, cwd: Path) -> None:
        super().__init__()
        self.settings = settings
        self.cwd = cwd
        self.chat_messages: list[str] = []
        self.status_message = self._startup_status()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(id="main-layout"):
            yield Static(self.status_message, id="session-status")
            yield RichLog(id="chat-history", highlight=False, markup=False, wrap=True)
            yield Input(placeholder="Ask CodeGopher...", id="prompt-input")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#prompt-input", Input).focus()

    def action_focus_input(self) -> None:
        self.query_one("#prompt-input", Input).focus()
        self.set_status("Input focused")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        prompt = event.value.strip()
        event.input.value = ""
        if not prompt:
            self.set_status("Enter a prompt to continue")
            return
        self.append_user_message(prompt)

    def append_user_message(self, content: str) -> None:
        message = f"You: {content}"
        self.chat_messages.append(message)
        self.query_one("#chat-history", RichLog).write(message, scroll_end=True)
        self.set_status("Prompt captured; agent streaming starts in a later v0.2 milestone")

    def set_status(self, message: str) -> None:
        self.status_message = message
        self.query_one("#session-status", Static).update(message)

    def _startup_status(self) -> str:
        model = self.settings.model.name
        provider = self.settings.model.provider
        approval = self.settings.approval_mode.value
        return f"Model: {model} | Provider: {provider} | Approval: {approval} | CWD: {self.cwd}"

