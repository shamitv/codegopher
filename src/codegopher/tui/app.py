"""Textual application shell for interactive CodeGopher sessions."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.widgets import Footer, Header, Input, RichLog, Static

from codegopher.config.schema import Settings
from codegopher.core.agent import AgentCallbacks, AgentResult, run_agent
from codegopher.core.errors import AgentLoopError, ProviderError
from codegopher.core.types import ToolCall
from codegopher.providers.base import Provider
from codegopher.runtime import build_provider
from codegopher.tools.base import ToolResult
from codegopher.tools.registry import ToolRegistry, create_default_registry

if TYPE_CHECKING:
    from textual.binding import BindingType


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

    #assistant-stream {
        min-height: 1;
        padding: 0 1;
    }

    #prompt-input {
        dock: bottom;
    }
    """
    BINDINGS: ClassVar[list[BindingType]] = [
        ("ctrl+q", "quit", "Quit"),
        ("ctrl+i", "focus_input", "Focus input"),
    ]

    def __init__(
        self,
        *,
        settings: Settings,
        cwd: Path,
        provider_factory: Callable[[Settings], Provider] = build_provider,
        registry_factory: Callable[[], ToolRegistry] = create_default_registry,
    ) -> None:
        super().__init__()
        self.settings = settings
        self.cwd = cwd
        self.provider_factory = provider_factory
        self.registry_factory = registry_factory
        self.chat_messages: list[str] = []
        self.status_message = self._startup_status()
        self.turn_running = False
        self._active_assistant_message = ""

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(id="main-layout"):
            yield Static(self.status_message, id="session-status")
            yield RichLog(id="chat-history", highlight=False, markup=False, wrap=True)
            yield Static("", id="assistant-stream")
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
        self._set_turn_running(True)
        self._active_assistant_message = ""
        self.query_one("#assistant-stream", Static).update("")
        self.set_status("Running agent turn...")
        self.run_worker(
            self._run_agent_turn(prompt),
            name="agent-turn",
            group="agent",
            exclusive=True,
            exit_on_error=False,
        )

    def append_user_message(self, content: str) -> None:
        self._append_chat_message(f"You: {content}")

    def append_system_message(self, content: str) -> None:
        self._append_chat_message(content)

    def set_status(self, message: str) -> None:
        self.status_message = message
        self.query_one("#session-status", Static).update(message)

    async def _run_agent_turn(self, prompt: str) -> None:
        callbacks = AgentCallbacks(
            on_text_delta=self._on_agent_text_delta,
            on_tool_call=self._on_agent_tool_call,
            on_tool_result=self._on_agent_tool_result,
            on_error=self._on_agent_error,
            on_complete=self._on_agent_complete,
        )
        try:
            await run_agent(
                prompt=prompt,
                provider=self.provider_factory(self.settings),
                registry=self.registry_factory(),
                settings=self.settings,
                cwd=self.cwd,
                stdin_is_tty=True,
                callbacks=callbacks,
            )
        except (AgentLoopError, ProviderError) as exc:
            message = f"Error: {exc}"
            self.append_system_message(message)
            self.set_status(message)
        finally:
            self._set_turn_running(False)

    async def _on_agent_text_delta(self, content: str) -> None:
        self._active_assistant_message += content
        self.query_one("#assistant-stream", Static).update(
            f"Assistant: {self._active_assistant_message}"
        )

    async def _on_agent_tool_call(self, tool_call: ToolCall) -> None:
        self.set_status(f"Tool requested: {tool_call['name']}")

    async def _on_agent_tool_result(self, result: ToolResult) -> None:
        state = "failed" if result.is_error else "completed"
        self.set_status(f"Tool {state}: {result.tool_call_id}")

    async def _on_agent_error(self, message: str) -> None:
        self.set_status(f"Error: {message}")

    async def _on_agent_complete(self, result: AgentResult) -> None:
        if self._active_assistant_message:
            self._append_chat_message(f"Assistant: {self._active_assistant_message}")
            self._active_assistant_message = ""
            self.query_one("#assistant-stream", Static).update("")
        elif result.final_text:
            self._append_chat_message(f"Assistant: {result.final_text}")
        self.set_status(f"Done after {result.iterations} iteration(s)")

    def _append_chat_message(self, message: str) -> None:
        self.chat_messages.append(message)
        self.query_one("#chat-history", RichLog).write(message, scroll_end=True)

    def _set_turn_running(self, running: bool) -> None:
        self.turn_running = running
        self.query_one("#prompt-input", Input).disabled = running

    def _startup_status(self) -> str:
        model = self.settings.model.name
        provider = self.settings.model.provider
        approval = self.settings.approval_mode.value
        return f"Model: {model} | Provider: {provider} | Approval: {approval} | CWD: {self.cwd}"
