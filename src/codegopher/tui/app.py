"""Textual application shell for interactive CodeGopher sessions."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from pathlib import Path
from time import monotonic
from typing import TYPE_CHECKING, ClassVar

from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.widgets import Button, Footer, Header, Input, RichLog, Static

from codegopher.config.schema import ApprovalMode, Settings
from codegopher.core.agent import AgentCallbacks, AgentResult, run_agent
from codegopher.core.approval import ApprovalRequest, ApprovalResult
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

    #approval-panel {
        height: auto;
        padding: 1;
        border-top: solid $warning;
    }

    #approval-reason {
        margin-top: 1;
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
        clock: Callable[[], float] = monotonic,
    ) -> None:
        super().__init__()
        self.settings = settings
        self.cwd = cwd
        self.provider_factory = provider_factory
        self.registry_factory = registry_factory
        self.clock = clock
        self.chat_messages: list[str] = []
        self.status_message = self._startup_status()
        self.turn_running = False
        self.turn_count = 0
        self.tool_count = 0
        self.approval_count = 0
        self.started_at = self.clock()
        self._active_assistant_message = ""
        self._tool_call_names: dict[str, str] = {}
        self._pending_approval: asyncio.Future[ApprovalResult] | None = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(id="main-layout"):
            yield Static(self.status_message, id="session-status")
            yield RichLog(id="chat-history", highlight=False, markup=False, wrap=True)
            yield Static("", id="assistant-stream")
            with Vertical(id="approval-panel"):
                yield Static("", id="approval-title")
                yield Static("", id="approval-arguments")
                yield Input(placeholder="Optional deny reason", id="approval-reason")
                yield Button("Approve", id="approval-approve", variant="success")
                yield Button("Deny", id="approval-deny", variant="error")
            yield Input(placeholder="Ask CodeGopher...", id="prompt-input")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#approval-panel", Vertical).display = False
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
        if self.turn_running:
            self.set_status("Wait for the current turn to finish")
            return
        if prompt.startswith("/"):
            self._handle_slash_command(prompt)
            return
        self.append_user_message(prompt)
        self._set_turn_running(True)
        self._active_assistant_message = ""
        self._tool_call_names = {}
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
            on_approval_request=self._on_agent_approval_request,
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
            self.turn_count += 1
            self._set_turn_running(False)

    async def _on_agent_text_delta(self, content: str) -> None:
        self._active_assistant_message += content
        self.query_one("#assistant-stream", Static).update(
            f"Assistant: {self._active_assistant_message}"
        )

    async def _on_agent_tool_call(self, tool_call: ToolCall) -> None:
        self._tool_call_names[tool_call["id"]] = tool_call["name"]
        arguments = self._summarize_arguments(tool_call["arguments"])
        suffix = f" {arguments}" if arguments else ""
        self.append_system_message(f"Tool requested: {tool_call['name']}{suffix}")
        self.set_status(f"Tool requested: {tool_call['name']}")

    async def _on_agent_tool_result(self, result: ToolResult) -> None:
        self.tool_count += 1
        tool_name = self._tool_call_names.get(result.tool_call_id, result.tool_call_id)
        state = "failed" if result.is_error else "completed"
        if result.is_error:
            self.append_system_message(f"Tool failed: {tool_name}: {result.content}")
        else:
            self.append_system_message(f"Tool completed: {tool_name}")
        self.set_status(f"Tool {state}: {tool_name}")

    async def _on_agent_approval_request(self, request: ApprovalRequest) -> ApprovalResult:
        loop = asyncio.get_running_loop()
        future: asyncio.Future[ApprovalResult] = loop.create_future()
        self._pending_approval = future
        self._show_approval_request(request)
        return await future

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

    def _show_approval_request(self, request: ApprovalRequest) -> None:
        self.query_one("#approval-title", Static).update(f"Approval required: {request.tool_name}")
        self.query_one("#approval-arguments", Static).update(
            self._shorten(request.arguments_preview)
        )
        self.query_one("#approval-reason", Input).value = ""
        self.query_one("#approval-panel", Vertical).display = True
        self.set_status(f"Approval required: {request.tool_name}")

    def _resolve_pending_approval(self, result: ApprovalResult) -> None:
        if self._pending_approval and not self._pending_approval.done():
            self._pending_approval.set_result(result)
            self.approval_count += 1
        self._pending_approval = None
        self.query_one("#approval-panel", Vertical).display = False

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "approval-approve":
            self._resolve_pending_approval(ApprovalResult(approved=True))
            self.set_status("Tool approved")
        elif event.button.id == "approval-deny":
            reason = self.query_one("#approval-reason", Input).value.strip() or "Denied by user"
            self._resolve_pending_approval(ApprovalResult(approved=False, reason=reason))
            self.set_status("Tool denied")

    def _set_turn_running(self, running: bool) -> None:
        self.turn_running = running
        self.query_one("#prompt-input", Input).disabled = running

    def _handle_slash_command(self, prompt: str) -> None:
        command_text = prompt[1:].strip()
        if not command_text:
            self._show_command_error("/")
            return
        command, _, arguments = command_text.partition(" ")
        arguments = arguments.strip()

        if command == "help":
            self._handle_help_command(arguments)
        elif command == "clear":
            self._handle_clear_command(arguments)
        elif command == "model":
            self._handle_model_command(arguments)
        elif command == "mode":
            self._handle_mode_command(arguments)
        elif command == "stats":
            self._handle_stats_command(arguments)
        else:
            self._show_command_error(f"/{command}")

    def _handle_help_command(self, arguments: str) -> None:
        if arguments:
            self._show_command_error("/help")
            return
        self.append_system_message(
            "Commands: /help show commands; /clear clear visible chat; "
            "/model [name] show or set model; /mode [review|auto|yolo] show or set approvals; "
            "/stats show session counters"
        )
        self.set_status("Help displayed")

    def _handle_clear_command(self, arguments: str) -> None:
        if arguments:
            self._show_command_error("/clear")
            return
        self.chat_messages.clear()
        self.query_one("#chat-history", RichLog).clear()
        self._active_assistant_message = ""
        self.query_one("#assistant-stream", Static).update("")
        self.set_status("Chat history cleared")

    def _handle_model_command(self, arguments: str) -> None:
        if not arguments:
            self.append_system_message(
                f"Model: {self.settings.model.provider}/{self.settings.model.name}"
            )
            self.set_status("Model displayed")
            return
        if len(arguments.split()) != 1:
            self._show_command_error("/model")
            return
        self.settings = self.settings.model_copy(
            update={"model": self.settings.model.model_copy(update={"name": arguments})}
        )
        self.append_system_message(
            f"Model updated: {self.settings.model.provider}/{self.settings.model.name}"
        )
        self.set_status(self._startup_status())

    def _handle_mode_command(self, arguments: str) -> None:
        if not arguments:
            self.append_system_message(f"Approval mode: {self.settings.approval_mode.value}")
            self.set_status("Approval mode displayed")
            return
        try:
            approval_mode = ApprovalMode(arguments)
        except ValueError:
            self._show_command_error("/mode")
            return
        self.settings = self.settings.model_copy(update={"approval_mode": approval_mode})
        self.append_system_message(f"Approval mode updated: {self.settings.approval_mode.value}")
        self.set_status(self._startup_status())

    def _handle_stats_command(self, arguments: str) -> None:
        if arguments:
            self._show_command_error("/stats")
            return
        elapsed = max(0.0, self.clock() - self.started_at)
        self.append_system_message(
            "Stats: "
            f"turns={self.turn_count}, tools={self.tool_count}, "
            f"approvals={self.approval_count}, elapsed={elapsed:.1f}s"
        )
        self.set_status("Stats displayed")

    def _show_command_error(self, command: str) -> None:
        message = f"Unknown command: {command}"
        self.append_system_message(message)
        self.set_status(message)

    def _summarize_arguments(self, arguments: dict[str, object]) -> str:
        if not arguments:
            return ""
        return self._shorten(str(arguments))

    def _shorten(self, value: str, limit: int = 240) -> str:
        if len(value) <= limit:
            return value
        return f"{value[: limit - 3]}..."

    def _startup_status(self) -> str:
        model = self.settings.model.name
        provider = self.settings.model.provider
        approval = self.settings.approval_mode.value
        return f"Model: {model} | Provider: {provider} | Approval: {approval} | CWD: {self.cwd}"
