from __future__ import annotations

from pathlib import Path

from codegopher.config.schema import ApprovalMode
from codegopher.core.context import build_messages, build_system_prompt
from codegopher.core.conversation import Conversation
from codegopher.tools.base import ToolResult
from codegopher.tools.registry import create_default_registry


def test_context_builder_includes_cwd_tools_and_approval_mode(tmp_path: Path) -> None:
    registry = create_default_registry()
    prompt = build_system_prompt(tmp_path, registry, ApprovalMode.review)

    assert str(tmp_path) in prompt
    assert "read_file" in prompt
    assert "Approval mode: review" in prompt


def test_context_builder_prepends_system_message(tmp_path: Path) -> None:
    conversation = Conversation()
    conversation.append_user("hello")

    messages = build_messages(
        conversation,
        cwd=tmp_path,
        registry=create_default_registry(),
        approval_mode=ApprovalMode.review,
    )

    assert messages[0]["role"] == "system"
    assert messages[1] == {"role": "user", "content": "hello"}


def test_context_builder_includes_selected_memories(tmp_path: Path) -> None:
    conversation = Conversation()

    messages = build_messages(
        conversation,
        cwd=tmp_path,
        registry=create_default_registry(),
        approval_mode=ApprovalMode.review,
        memories=["[project:mem-1] Use pytest"],
    )

    assert "Selected memories" in str(messages[0]["content"])
    assert "[project:mem-1] Use pytest" in str(messages[0]["content"])


def test_context_builder_includes_loaded_skills(tmp_path: Path) -> None:
    conversation = Conversation()

    messages = build_messages(
        conversation,
        cwd=tmp_path,
        registry=create_default_registry(),
        approval_mode=ApprovalMode.review,
        skills=["## Pytest (project:pytest)\nPrefer focused tests."],
    )

    assert "Loaded skills" in str(messages[0]["content"])
    assert "Prefer focused tests." in str(messages[0]["content"])


def test_context_builder_includes_active_todos(tmp_path: Path) -> None:
    conversation = Conversation()

    messages = build_messages(
        conversation,
        cwd=tmp_path,
        registry=create_default_registry(),
        approval_mode=ApprovalMode.review,
        todo_items=["[todo-1] pending: Write TODO tests"],
    )

    assert "Active TODOs" in str(messages[0]["content"])
    assert "[todo-1] pending: Write TODO tests" in str(messages[0]["content"])


def test_context_builder_includes_runtime_episode_memory(tmp_path: Path) -> None:
    conversation = Conversation()

    messages = build_messages(
        conversation,
        cwd=tmp_path,
        registry=create_default_registry(),
        approval_mode=ApprovalMode.review,
        episode_items=["[episode-1] file_read: Read app.py"],
    )

    assert "Runtime episode memory" in str(messages[0]["content"])
    assert "[episode-1] file_read: Read app.py" in str(messages[0]["content"])
    assert "not persistent memory" in str(messages[0]["content"])


def test_context_builder_keeps_loaded_skills_before_volatile_context(
    tmp_path: Path,
) -> None:
    prompt = build_system_prompt(
        tmp_path,
        create_default_registry(),
        ApprovalMode.review,
        memories=["[project:mem-1] Volatile memory"],
        episode_items=["[episode-1] Read app.py"],
        skills=["## Audit Skill\nStable skill text."],
        todo_items=["[todo-1] pending: Re-check report"],
        mission_items=["write docs/security/CHAINED_VULNERABILITIES_REVIEW.md"],
    )

    assert prompt.index("Loaded skills") < prompt.index("Selected memories")
    assert prompt.index("Loaded skills") < prompt.index("Runtime episode memory")
    assert prompt.index("Loaded skills") < prompt.index("Active TODOs")
    assert prompt.index("Loaded skills") < prompt.index("Active mission contract")


def test_context_builder_mentions_only_implemented_v0_1_features(tmp_path: Path) -> None:
    prompt = build_system_prompt(tmp_path, create_default_registry(), ApprovalMode.review)

    assert "save_memory" in prompt
    for future_feature in ("TUI", "MCP", "sub-agents"):
        assert future_feature not in prompt
    assert "Loaded skills" not in prompt


def test_context_builder_replay_message_cap_keeps_recent_messages(tmp_path: Path) -> None:
    conversation = Conversation()
    conversation.append_user("one")
    conversation.append_user("two")
    conversation.append_user("three")

    messages = build_messages(
        conversation,
        cwd=tmp_path,
        registry=create_default_registry(),
        approval_mode=ApprovalMode.review,
        max_replay_messages=2,
    )

    assert messages[0]["role"] == "system"
    assert messages[1] == {"role": "user", "content": "two"}
    assert messages[2] == {"role": "user", "content": "three"}


def test_context_builder_replay_message_cap_preserves_tool_turn_boundary(
    tmp_path: Path,
) -> None:
    conversation = Conversation()
    conversation.append_user("inspect")
    conversation.append_assistant(
        None,
        [
            {
                "id": "call-1",
                "name": "read_file",
                "arguments": {"path": "README.md"},
            }
        ],
    )
    conversation.append_tool_result(
        ToolResult(tool_call_id="call-1", content="project notes")
    )

    messages = build_messages(
        conversation,
        cwd=tmp_path,
        registry=create_default_registry(),
        approval_mode=ApprovalMode.review,
        max_replay_messages=1,
    )

    assert [message["role"] for message in messages] == ["system", "assistant", "tool"]
    assert messages[1]["tool_calls"][0]["id"] == "call-1"
    assert messages[2]["tool_call_id"] == "call-1"


def test_context_builder_replay_message_cap_preserves_response_item_tool_boundary(
    tmp_path: Path,
) -> None:
    conversation = Conversation()
    conversation.append_user("inspect")
    conversation.append_assistant(
        None,
        response_items=[
            {
                "type": "function_call",
                "id": "fc-1",
                "call_id": "call-1",
                "name": "read_file",
                "arguments": '{"path":"README.md"}',
            }
        ],
    )
    conversation.append_tool_result(
        ToolResult(tool_call_id="call-1", content="project notes")
    )

    messages = build_messages(
        conversation,
        cwd=tmp_path,
        registry=create_default_registry(),
        approval_mode=ApprovalMode.review,
        max_replay_messages=1,
    )

    assert [message["role"] for message in messages] == ["system", "assistant", "tool"]
    assert messages[1]["response_items"][0]["call_id"] == "call-1"
    assert messages[2]["tool_call_id"] == "call-1"
