"""Textual application shell for interactive CodeGopher sessions."""

from __future__ import annotations

import asyncio
import time
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.widgets import Button, Footer, Header, Input, RichLog, Static

from codegopher.config.schema import ApprovalMode, Settings
from codegopher.core.agent import AgentCallbacks, AgentResult, AgentSession
from codegopher.core.approval import ApprovalRequest, ApprovalResult, should_prompt
from codegopher.core.context import build_messages
from codegopher.core.context_budget import calculate_context_budget
from codegopher.core.conversation import Conversation
from codegopher.core.errors import AgentLoopError, ProviderError
from codegopher.core.types import CompactionEntry, Message, ToolCall
from codegopher.providers.base import Provider
from codegopher.runtime import build_provider
from codegopher.tools.base import ToolContext, ToolResult
from codegopher.tools.registry import ToolRegistry, create_default_registry
from codegopher.tools.shell.run_shell import RunShellCommandTool
from codegopher.tui.commands import COMMAND_DEFINITIONS, SlashCommand, parse_slash_command
from codegopher.tui.mentions import MentionExpansion, expand_mentions
from codegopher.tui.session import MessageRole, SessionMessage, TuiSessionState, TuiSessionStore
from codegopher.utils.json import dumps_json

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

    #reasoning-stream {
        min-height: 1;
        padding: 0 1;
        color: $text-muted;
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
        monotonic: Callable[[], float] = time.monotonic,
        session_store: TuiSessionStore | None = None,
        session_state: TuiSessionState | None = None,
        session_load_error: str | None = None,
        shell_timeout_seconds: int = 30,
    ) -> None:
        super().__init__()
        self.settings = settings
        self.cwd = cwd
        self.provider_factory = provider_factory
        self.registry = registry_factory()
        self.tool_context = ToolContext(cwd=cwd)
        self._agent_session: AgentSession | None = None
        self.session_store = session_store
        self.session_state = session_state or (
            session_store.create(cwd=cwd, settings=settings) if session_store else None
        )
        self.session_load_error = session_load_error
        self.shell_timeout_seconds = shell_timeout_seconds
        self.monotonic = monotonic
        self.started_at = monotonic()
        self.chat_messages: list[str] = (
            [message.content for message in self.session_state.messages]
            if self.session_state
            else []
        )
        self.status_message = self._startup_status()
        self.turn_running = False
        self.turn_count = 0
        self.tool_count = 0
        self.approval_count = 0
        self._active_reasoning_message = ""
        self._active_assistant_message = ""
        self._tool_call_names: dict[str, str] = {}
        self._pending_approval: asyncio.Future[ApprovalResult] | None = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(id="main-layout"):
            yield Static(self.status_message, id="session-status")
            yield RichLog(id="chat-history", highlight=False, markup=False, wrap=True)
            yield Static("", id="reasoning-stream")
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
        self.query_one("#reasoning-stream", Static).display = False
        history = self.query_one("#chat-history", RichLog)
        for message in self.chat_messages:
            history.write(message, scroll_end=True)
        if self.session_load_error:
            self.append_system_message(f"Session resume failed: {self.session_load_error}")
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

        command = parse_slash_command(prompt)
        if command is not None:
            self._handle_slash_command(command)
            return

        expansion = self._expand_prompt_mentions(prompt)
        self.append_user_message(prompt)
        if expansion.has_mentions:
            self.append_system_message(expansion.summary())
        if expansion.has_errors:
            self.set_status("Mention expansion failed")
            return

        self.turn_count += 1
        self._set_turn_running(True)
        self._active_reasoning_message = ""
        self._active_assistant_message = ""
        self._tool_call_names = {}
        self.query_one("#reasoning-stream", Static).display = False
        self.query_one("#reasoning-stream", Static).update("")
        self.query_one("#assistant-stream", Static).update("")
        self.set_status("Running agent turn...")
        self.run_worker(
            self._run_agent_turn(expansion.prompt),
            name="agent-turn",
            group="agent",
            exclusive=True,
            exit_on_error=False,
        )

    def append_user_message(self, content: str) -> None:
        self._append_chat_message(f"You: {content}", role="user")

    def append_system_message(self, content: str) -> None:
        self._append_chat_message(content, role="system")

    def set_status(self, message: str) -> None:
        self.status_message = message
        self.query_one("#session-status", Static).update(message)

    async def _run_agent_turn(self, prompt: str) -> None:
        callbacks = AgentCallbacks(
            on_text_delta=self._on_agent_text_delta,
            on_reasoning_delta=self._on_agent_reasoning_delta,
            on_tool_call=self._on_agent_tool_call,
            on_tool_result=self._on_agent_tool_result,
            on_approval_request=self._on_agent_approval_request,
            on_compaction=self._on_agent_compaction,
            on_error=self._on_agent_error,
            on_complete=self._on_agent_complete,
        )
        try:
            await self._ensure_agent_session(callbacks).run_turn(prompt)
        except (AgentLoopError, ProviderError) as exc:
            message = f"Error: {exc}"
            self.append_system_message(message)
            self.set_status(message)
        finally:
            self._set_turn_running(False)

    def _ensure_agent_session(self, callbacks: AgentCallbacks) -> AgentSession:
        if self._agent_session is None:
            self._agent_session = AgentSession(
                provider=self.provider_factory(self.settings),
                registry=self.registry,
                settings=self.settings,
                cwd=self.cwd,
                stdin_is_tty=True,
                callbacks=callbacks,
                tool_context=self.tool_context,
                conversation=Conversation(
                    messages=list(self.session_state.provider_messages)
                    if self.session_state
                    else []
                ),
            )
            self.tool_context = self._agent_session.tool_context
        else:
            self._agent_session.callbacks = callbacks
        return self._agent_session

    async def _on_agent_text_delta(self, content: str) -> None:
        self._active_assistant_message += content
        self.query_one("#assistant-stream", Static).update(
            f"Assistant: {self._active_assistant_message}"
        )

    async def _on_agent_reasoning_delta(self, content: str) -> None:
        self._active_reasoning_message += content
        reasoning_stream = self.query_one("#reasoning-stream", Static)
        reasoning_stream.display = True
        reasoning_stream.update(
            f"Reasoning (collapsed): {len(self._active_reasoning_message)} chars"
        )

    async def _on_agent_tool_call(self, tool_call: ToolCall) -> None:
        self.tool_count += 1
        self._tool_call_names[tool_call["id"]] = tool_call["name"]
        arguments = self._summarize_arguments(tool_call["arguments"])
        suffix = f" {arguments}" if arguments else ""
        self.append_system_message(f"Tool requested: {tool_call['name']}{suffix}")
        self.set_status(f"Tool requested: {tool_call['name']}")

    async def _on_agent_tool_result(self, result: ToolResult) -> None:
        tool_name = self._tool_call_names.get(result.tool_call_id, result.tool_call_id)
        state = "failed" if result.is_error else "completed"
        if result.is_error:
            self.append_system_message(f"Tool failed: {tool_name}: {result.content}")
        else:
            self.append_system_message(f"Tool completed: {tool_name}")
        self.set_status(f"Tool {state}: {tool_name}")

    async def _on_agent_approval_request(self, request: ApprovalRequest) -> ApprovalResult:
        self.approval_count += 1
        return await self._request_tui_approval(request)

    async def _on_agent_compaction(self, entry: CompactionEntry) -> None:
        self.append_system_message(f"Context compacted ({entry.reason}): {entry.summary}")
        self.set_status("Context compacted")

    async def _on_agent_error(self, message: str) -> None:
        self.set_status(f"Error: {message}")

    async def _on_agent_complete(self, result: AgentResult) -> None:
        if self._active_reasoning_message:
            self._append_chat_message(
                f"Reasoning (collapsed): {self._active_reasoning_message}",
                role="system",
            )
            self._active_reasoning_message = ""
            self.query_one("#reasoning-stream", Static).display = False
            self.query_one("#reasoning-stream", Static).update("")
        if self._active_assistant_message:
            self._append_chat_message(
                f"Assistant: {self._active_assistant_message}",
                role="assistant",
            )
            self._active_assistant_message = ""
            self.query_one("#assistant-stream", Static).update("")
        elif result.final_text:
            self._append_chat_message(f"Assistant: {result.final_text}", role="assistant")
        self.set_status(f"Done after {result.iterations} iteration(s)")

    def _append_chat_message(self, message: str, *, role: MessageRole = "system") -> None:
        self.chat_messages.append(message)
        if self.session_state is not None:
            self.session_state.messages.append(SessionMessage(role=role, content=message))
            self._persist_session()
        self.query_one("#chat-history", RichLog).write(message, scroll_end=True)

    def _persist_session(self) -> None:
        if not self.session_store or not self.session_state:
            return
        if self._agent_session is not None:
            self.session_state.provider_messages = (
                self._agent_session.conversation.provider_messages()
            )
        try:
            self.session_store.save(self.session_state, settings=self.settings)
        except OSError as exc:
            self.status_message = f"Session save failed: {exc}"

    def _expand_prompt_mentions(self, prompt: str) -> MentionExpansion:
        return expand_mentions(
            prompt,
            cwd=self.cwd,
            tool_context=self.tool_context,
            ignore_file=self.settings.ignore_file,
        )

    def _handle_slash_command(self, command: SlashCommand) -> None:
        if command.name == "help":
            self._handle_help_command(command)
        elif command.name == "clear":
            self._handle_clear_command(command)
        elif command.name == "compact":
            self._handle_compact_command(command)
        elif command.name == "model":
            self._handle_model_command(command)
        elif command.name == "mode":
            self._handle_mode_command(command)
        elif command.name == "shell":
            self._handle_shell_command(command)
        elif command.name == "stats":
            self._handle_stats_command(command)
        else:
            unknown = command.raw.split(maxsplit=1)[0]
            self._command_error(f"Unknown slash command: {unknown}")

    def _handle_help_command(self, command: SlashCommand) -> None:
        if command.arguments:
            self._command_error("Usage: /help")
            return
        lines = ["Slash commands:"]
        lines.extend(
            f"{definition.usage} - {definition.description}"
            for definition in COMMAND_DEFINITIONS
        )
        self.append_system_message("\n".join(lines))
        self.set_status("Displayed help")

    def _handle_clear_command(self, command: SlashCommand) -> None:
        if command.arguments:
            self._command_error("Usage: /clear")
            return
        self.chat_messages.clear()
        self._active_assistant_message = ""
        self.query_one("#chat-history", RichLog).clear()
        self.query_one("#assistant-stream", Static).update("")
        self.set_status("Chat history cleared")

    def _handle_compact_command(self, command: SlashCommand) -> None:
        if self.turn_running:
            self._command_error("Cannot compact while a turn is running")
            return
        if not self._provider_conversation_messages():
            self.append_system_message("Nothing to compact")
            self.set_status("Nothing to compact")
            return
        instructions = command.arguments or None
        self._set_turn_running(True)
        self.set_status("Compacting context...")
        self.run_worker(
            self._run_manual_compaction(instructions),
            name="manual-compaction",
            group="agent",
            exclusive=True,
            exit_on_error=False,
        )

    async def _run_manual_compaction(self, instructions: str | None) -> None:
        try:
            entry = await self._ensure_agent_session(AgentCallbacks()).compact(
                instructions=instructions,
                reason="manual",
            )
        except ProviderError as exc:
            message = f"Compaction failed: {exc}"
            self.append_system_message(message)
            self.set_status(message)
        else:
            self.append_system_message(
                f"Context compacted ({entry.reason}): {entry.summary}"
            )
            self.set_status("Context compacted")
        finally:
            self._set_turn_running(False)

    def _handle_model_command(self, command: SlashCommand) -> None:
        if not command.arguments:
            message = (
                f"Model: {self.settings.model.name} | "
                f"Provider: {self.settings.model.provider}"
            )
            self.append_system_message(message)
            self.set_status("Displayed active model")
            return

        self.settings.model.name = command.arguments
        message = (
            f"Model updated: {self.settings.model.name} | "
            f"Provider: {self.settings.model.provider}"
        )
        self.append_system_message(message)
        self.set_status(message)

    def _handle_mode_command(self, command: SlashCommand) -> None:
        if not command.arguments:
            message = f"Approval mode: {self.settings.approval_mode.value}"
            self.append_system_message(message)
            self.set_status("Displayed approval mode")
            return

        try:
            mode = ApprovalMode(command.arguments)
        except ValueError:
            self._command_error("Usage: /mode review|auto|yolo")
            return

        self.settings.approval_mode = mode
        message = f"Approval mode updated: {mode.value}"
        self.append_system_message(message)
        self.set_status(message)

    def _handle_shell_command(self, command: SlashCommand) -> None:
        if not command.arguments:
            self._command_error("Usage: /shell COMMAND")
            return
        self.tool_count += 1
        self.append_system_message(f"Shell requested: {command.arguments}")
        self._set_turn_running(True)
        self.run_worker(
            self._run_shell_passthrough(command.arguments),
            name="shell-passthrough",
            group="shell",
            exclusive=True,
            exit_on_error=False,
        )

    def _handle_stats_command(self, command: SlashCommand) -> None:
        if command.arguments:
            self._command_error("Usage: /stats")
            return
        elapsed_seconds = max(0, int(self.monotonic() - self.started_at))
        message = (
            f"Stats: turns={self.turn_count} | tools={self.tool_count} | "
            f"approvals={self.approval_count} | elapsed={elapsed_seconds}s | "
            f"{self._context_budget_summary()}"
        )
        self.append_system_message(message)
        self.set_status("Displayed stats")

    def _context_budget_summary(self) -> str:
        messages = build_messages(
            Conversation(messages=self._provider_conversation_messages()),
            cwd=self.cwd,
            registry=self.registry,
            approval_mode=self.settings.approval_mode,
        )
        budget = calculate_context_budget(messages, settings=self.settings)
        if budget.context_window is None:
            return f"context={budget.token_count} tokens (window unknown)"
        state = (
            "compact"
            if budget.compaction_exceeded
            else "warn"
            if budget.warning_exceeded
            else "ok"
        )
        percent = int((budget.usage_ratio or 0) * 100)
        return f"context={budget.token_count}/{budget.context_window} tokens ({percent}%, {state})"

    def _provider_conversation_messages(self) -> list[Message]:
        if self._agent_session is not None:
            return self._agent_session.conversation.provider_messages()
        if self.session_state:
            return list(self.session_state.provider_messages)
        return []

    def _command_error(self, message: str) -> None:
        full_message = f"Error: {message}"
        self.append_system_message(full_message)
        self.set_status(full_message)

    async def _run_shell_passthrough(self, command: str) -> None:
        shell_tool = RunShellCommandTool()
        try:
            approval = ApprovalResult(approved=True)
            if should_prompt(self.settings.approval_mode, shell_tool):
                self.approval_count += 1
                approval = await self._request_tui_approval(
                    ApprovalRequest(
                        tool_name=shell_tool.name,
                        arguments_preview=dumps_json({"command": command}),
                    )
                )
            if not approval.approved:
                reason = approval.reason or "Denied by user"
                self.append_system_message(f"Shell denied: {reason}")
                self.set_status("Shell denied")
                return

            result = await shell_tool.execute(
                {
                    "command": command,
                    "timeout_seconds": self.shell_timeout_seconds,
                    "_tool_call_id": "shell-passthrough",
                },
                self.tool_context,
            )
            state = "failed" if result.is_error else "completed"
            self.append_system_message(f"Shell {state}:\n{result.content}")
            self.set_status(f"Shell {state}")
        finally:
            self._set_turn_running(False)

    def _show_approval_request(self, request: ApprovalRequest) -> None:
        self.query_one("#approval-title", Static).update(f"Approval required: {request.tool_name}")
        self.query_one("#approval-arguments", Static).update(
            self._shorten(request.arguments_preview)
        )
        self.query_one("#approval-reason", Input).value = ""
        self.query_one("#approval-panel", Vertical).display = True
        self.set_status(f"Approval required: {request.tool_name}")

    async def _request_tui_approval(self, request: ApprovalRequest) -> ApprovalResult:
        loop = asyncio.get_running_loop()
        future: asyncio.Future[ApprovalResult] = loop.create_future()
        self._pending_approval = future
        self._show_approval_request(request)
        return await future

    def _resolve_pending_approval(self, result: ApprovalResult) -> None:
        if self._pending_approval and not self._pending_approval.done():
            self._pending_approval.set_result(result)
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
