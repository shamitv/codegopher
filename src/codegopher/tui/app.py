"""Textual application shell for interactive CodeGopher sessions."""

from __future__ import annotations

import asyncio
import os
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
from codegopher.core.errors import AgentLoopError, ConfigurationError, ProviderError
from codegopher.core.types import (
    CompactionEntry,
    MemoryEntry,
    MemoryScope,
    Message,
    SkillSource,
    TodoItem,
    ToolCall,
)
from codegopher.mcp import McpManager
from codegopher.memory import MemoryStore
from codegopher.providers.base import Provider
from codegopher.runtime import build_provider
from codegopher.skills import Skill, SkillDiscovery, SkillManager, discover_skills
from codegopher.todo import TodoState
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
        mcp_manager_factory: Callable[[Settings, Path], McpManager] | None = None,
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
        self.mcp_manager_factory = mcp_manager_factory or (
            lambda settings, cwd: McpManager(settings=settings, cwd=cwd, environ=os.environ)
        )
        self.mcp_manager: McpManager | None = None
        self._agent_session: AgentSession | None = None
        self.session_store = session_store
        self.session_state = session_state or (
            session_store.create(cwd=cwd, settings=settings) if session_store else None
        )
        self.registry = registry_factory()
        self.skill_discovery: SkillDiscovery = discover_skills(cwd=cwd, settings=settings)
        self.skill_manager = SkillManager(
            self.skill_discovery.catalog,
            loaded_ids=self.session_state.loaded_skill_ids if self.session_state else (),
            autoload=settings.skills.autoload,
        )
        self.todo_state = TodoState(
            items=self.session_state.todo_items if self.session_state else [],
            max_items=settings.todo.max_items,
        )
        memory_store = MemoryStore(data_home=session_store.data_home) if session_store else None
        self.tool_context = ToolContext(
            cwd=cwd,
            settings=settings,
            memory_store=memory_store,
            todo_state=self.todo_state,
            session_id=self.session_state.session_id if self.session_state else None,
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

    async def on_mount(self) -> None:
        self.query_one("#approval-panel", Vertical).display = False
        self.query_one("#reasoning-stream", Static).display = False
        history = self.query_one("#chat-history", RichLog)
        for message in self.chat_messages:
            history.write(message, scroll_end=True)
        if self.session_load_error:
            self.append_system_message(f"Session resume failed: {self.session_load_error}")
        await self._initialize_mcp()
        self.query_one("#prompt-input", Input).focus()

    async def on_unmount(self) -> None:
        if self.mcp_manager is not None:
            await self.mcp_manager.aclose()

    async def _initialize_mcp(self) -> None:
        if not self.settings.mcp.enabled:
            return
        self.mcp_manager = self.mcp_manager_factory(self.settings, self.cwd)
        try:
            await self.mcp_manager.start()
            self.mcp_manager.register_tools(self.registry)
        except ConfigurationError as exc:
            message = f"MCP initialization failed: {exc}"
            self.append_system_message(message)
            self.set_status(message)
            self.query_one("#prompt-input", Input).disabled = True

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
            self._persist_session()
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
                skill_manager=self.skill_manager,
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
        elif tool_name == "save_memory":
            self.append_system_message(self._format_memory_save_event(result.content))
        elif tool_name == "update_todo":
            self.append_system_message(self._format_todo_tool_event(result.content))
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
        self.session_state.loaded_skill_ids = list(self.skill_manager.loaded_ids)
        self.session_state.todo_items = self.todo_state.list()
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
        elif command.name == "forget":
            self._handle_forget_command(command)
        elif command.name == "memory":
            self._handle_memory_command(command)
        elif command.name == "model":
            self._handle_model_command(command)
        elif command.name == "mode":
            self._handle_mode_command(command)
        elif command.name == "shell":
            self._handle_shell_command(command)
        elif command.name == "skills":
            self._handle_skills_command(command)
        elif command.name == "stats":
            self._handle_stats_command(command)
        elif command.name == "todo":
            self._handle_todo_command(command)
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

    def _handle_forget_command(self, command: SlashCommand) -> None:
        parsed = self._parse_forget_arguments(command.arguments)
        if parsed is None:
            self._command_error("Usage: /forget ID [--yes]")
            return
        entry_id, confirmed = parsed
        if not self.settings.memory.enabled:
            self._command_error("Memory is disabled")
            return

        found = self._find_memory_entry(entry_id)
        if found is None:
            self._command_error(f"Memory not found: {entry_id}")
            return

        scope, entry = found
        if not confirmed:
            message = f"Confirm forget {entry.id}: run /forget {entry.id} --yes"
            self.append_system_message(message)
            self.set_status("Memory forget needs confirmation")
            return

        store = self.tool_context.memory_store or MemoryStore.default()
        deleted = store.delete_entry(
            scope,
            entry.id,
            session_id=self.tool_context.session_id if scope == "session" else None,
            cwd=self.cwd if scope == "project" else None,
        )
        if not deleted:
            self._command_error(f"Memory not found: {entry.id}")
            return
        self.append_system_message(self._format_memory_delete_event(entry))
        self.set_status("Memory deleted")

    def _parse_forget_arguments(self, arguments: str) -> tuple[str, bool] | None:
        parts = arguments.split()
        if len(parts) == 1:
            return parts[0], False
        if len(parts) == 2 and parts[1] == "--yes":
            return parts[0], True
        return None

    def _handle_memory_command(self, command: SlashCommand) -> None:
        if command.arguments:
            self._command_error("Usage: /memory")
            return
        self.append_system_message(self._format_memory_listing())
        self.set_status("Displayed memory")

    def _format_memory_listing(self) -> str:
        if not self.settings.memory.enabled:
            return "Memory is disabled"
        lines = ["Memories:"]
        lines.extend(self._format_memory_scope("Session", "session"))
        lines.extend(self._format_memory_scope("Project", "project"))
        return "\n".join(lines)

    def _format_memory_scope(self, label: str, scope: MemoryScope) -> list[str]:
        if scope == "session":
            if not self.settings.memory.session_enabled:
                return [f"{label}: disabled"]
            if not self.tool_context.session_id:
                return [f"{label}: unavailable"]
        if scope == "project" and not self.settings.memory.project_enabled:
            return [f"{label}: disabled"]

        entries = self._list_memory_entries(scope)
        if not entries:
            return [f"{label}: none"]
        return [
            f"{label} ({len(entries)}):",
            *[self._format_memory_entry(entry) for entry in entries],
        ]

    def _list_memory_entries(self, scope: MemoryScope) -> list[MemoryEntry]:
        store = self.tool_context.memory_store or MemoryStore.default()
        if scope == "session":
            if not self.tool_context.session_id:
                return []
            return store.list_entries("session", session_id=self.tool_context.session_id)
        return store.list_entries("project", cwd=self.cwd)

    def _find_memory_entry(self, entry_id: str) -> tuple[MemoryScope, MemoryEntry] | None:
        scopes: tuple[MemoryScope, MemoryScope] = ("session", "project")
        for scope in scopes:
            if scope == "session" and not self.settings.memory.session_enabled:
                continue
            if scope == "project" and not self.settings.memory.project_enabled:
                continue
            for entry in self._list_memory_entries(scope):
                if entry.id == entry_id:
                    return scope, entry
        return None

    def _format_memory_entry(self, entry: MemoryEntry) -> str:
        return f"- {entry.id} [{entry.scope}/{entry.source}] {entry.content}"

    def _format_memory_save_event(self, content: str) -> str:
        prefix = "Saved "
        separator = " memory "
        if content.startswith(prefix) and separator in content:
            scope, entry_id = content[len(prefix) :].split(separator, maxsplit=1)
            if scope in {"session", "project"} and entry_id:
                return f"Memory saved: {entry_id} ({scope})"
        return f"Memory saved: {content}"

    def _format_memory_delete_event(self, entry: MemoryEntry) -> str:
        return f"Memory deleted: {entry.id} [{entry.scope}/{entry.source}] {entry.content}"

    def _format_todo_tool_event(self, content: str) -> str:
        added_prefix = "Added TODO "
        updated_prefix = "Updated TODO "
        if content.startswith(added_prefix):
            item_id = content[len(added_prefix) :].strip()
            item = self._find_todo_item(item_id)
            if item is not None:
                return f"TODO added: {item.id} {item.text}"
            return f"TODO added: {item_id}"

        if content.startswith(updated_prefix) and " to " in content:
            item_id, status = content[len(updated_prefix) :].split(" to ", maxsplit=1)
            item = self._find_todo_item(item_id.strip())
            if item is not None and item.status == "done":
                return f"TODO done: {item.id} {item.text}"
            if item is not None:
                return f"TODO updated: {item.id} [{item.status}] {item.text}"
            return f"TODO updated: {item_id.strip()} [{status.strip()}]"

        return f"TODO updated: {content}"

    def _find_todo_item(self, item_id: str) -> TodoItem | None:
        for item in self.todo_state.list():
            if item.id == item_id:
                return item
        return None

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

    def _handle_skills_command(self, command: SlashCommand) -> None:
        if not self.settings.skills.enabled:
            self.append_system_message("Skills are disabled")
            self.set_status("Skills disabled")
            return
        if not command.arguments:
            self.append_system_message(self._format_skills_listing())
            self.set_status("Displayed skills")
            return

        parts = command.arguments.split()
        if len(parts) != 2 or parts[0] != "load":
            self._command_error("Usage: /skills [load ID]")
            return

        skill_id = parts[1]
        result = self.skill_manager.load(skill_id)
        if result.missing:
            self._command_error(f"Skill not found: {skill_id}")
            return
        if result.already_loaded:
            self.append_system_message(f"Skill already loaded: {skill_id}")
            self.set_status("Skill already loaded")
            return

        skill = result.loaded[0]
        self.append_system_message(
            f"Skill loaded: {skill.id} ({skill.source}) {skill.metadata.name}"
        )
        self._persist_session()
        self.set_status("Skill loaded")

    def _format_skills_listing(self) -> str:
        lines = ["Skills:"]
        sources: tuple[SkillSource, ...] = ("project", "user", "builtin")
        for source in sources:
            skills = self.skill_discovery.catalog.by_source(source)
            label = source.title()
            if not skills:
                lines.append(f"{label}: none")
                continue
            lines.append(f"{label} ({len(skills)}):")
            lines.extend(self._format_skill_entry(skill) for skill in skills)
        if self.skill_discovery.warnings:
            lines.append("Warnings:")
            lines.extend(f"- {warning}" for warning in self.skill_discovery.warnings)
        return "\n".join(lines)

    def _format_skill_entry(self, skill: Skill) -> str:
        state = "loaded" if skill.id in self.skill_manager.loaded_ids else "available"
        description = (
            f" - {skill.metadata.description}" if skill.metadata.description else ""
        )
        keywords = (
            f" (keywords: {', '.join(skill.metadata.keywords)})"
            if skill.metadata.keywords
            else ""
        )
        return f"- {skill.id} [{state}] {skill.metadata.name}{description}{keywords}"

    def _handle_stats_command(self, command: SlashCommand) -> None:
        if command.arguments:
            self._command_error("Usage: /stats")
            return
        elapsed_seconds = max(0, int(self.monotonic() - self.started_at))
        message = (
            f"Stats: turns={self.turn_count} | tools={self.tool_count} | "
            f"approvals={self.approval_count} | elapsed={elapsed_seconds}s | "
            f"{self._memory_count_summary()} | {self._context_budget_summary()}"
        )
        self.append_system_message(message)
        self.set_status("Displayed stats")

    def _handle_todo_command(self, command: SlashCommand) -> None:
        if not command.arguments:
            self.append_system_message(self._format_todo_listing())
            self.set_status("Displayed TODO")
            return

        parts = command.arguments.split(maxsplit=1)
        subcommand = parts[0]
        if subcommand == "add":
            if len(parts) != 2 or not parts[1].strip():
                self._command_error("Usage: /todo add TEXT")
                return
            self._add_todo_item(parts[1])
            return

        if subcommand == "done":
            if len(parts) != 2 or not parts[1].strip():
                self._command_error("Usage: /todo done ID")
                return
            self._complete_todo_item(parts[1])
            return

        self._command_error("Usage: /todo")

    def _add_todo_item(self, text: str) -> None:
        if not self.settings.todo.enabled:
            self._command_error("TODO is disabled")
            return
        try:
            item = self.todo_state.add(text, source="user")
        except ValueError as exc:
            self._command_error(str(exc))
            return
        self.append_system_message(f"TODO added: {item.id} {item.text}")
        self._persist_session()
        self.set_status("TODO added")

    def _complete_todo_item(self, item_id: str) -> None:
        if not self.settings.todo.enabled:
            self._command_error("TODO is disabled")
            return
        try:
            item = self.todo_state.done(item_id)
        except KeyError:
            self._command_error(f"TODO not found: {item_id}")
            return
        self.append_system_message(f"TODO done: {item.id} {item.text}")
        self._persist_session()
        self.set_status("TODO done")

    def _format_todo_listing(self) -> str:
        if not self.settings.todo.enabled:
            return "TODO is disabled"
        items = self.todo_state.list()
        if not items:
            return "TODO:\n- none"
        return "\n".join(
            [
                "TODO:",
                *[
                    f"- {item.id} [{item.status}] {item.text}"
                    for item in items
                ],
            ]
        )

    def _memory_count_summary(self) -> str:
        if not self.settings.memory.enabled:
            return "memory=disabled"
        session_count = (
            len(self._list_memory_entries("session"))
            if self.settings.memory.session_enabled and self.tool_context.session_id
            else 0
        )
        project_count = (
            len(self._list_memory_entries("project"))
            if self.settings.memory.project_enabled
            else 0
        )
        return (
            f"memory={session_count + project_count} "
            f"(session={session_count}, project={project_count})"
        )

    def _context_budget_summary(self) -> str:
        messages = build_messages(
            Conversation(messages=self._provider_conversation_messages()),
            cwd=self.cwd,
            registry=self.registry,
            approval_mode=self.settings.approval_mode,
            skills=self.skill_manager.context_items(),
            todo_items=self.todo_state.context_items()
            if self.settings.todo.enabled
            else (),
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
