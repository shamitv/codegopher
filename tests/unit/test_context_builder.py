from __future__ import annotations

from pathlib import Path

from codegopher.config.schema import ApprovalMode
from codegopher.core.context import build_messages, build_system_prompt
from codegopher.core.conversation import Conversation
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


def test_context_builder_mentions_only_implemented_v0_1_features(tmp_path: Path) -> None:
    prompt = build_system_prompt(tmp_path, create_default_registry(), ApprovalMode.review)

    assert "save_memory" in prompt
    for future_feature in ("TUI", "MCP", "sub-agents"):
        assert future_feature not in prompt
    assert "Loaded skills" not in prompt
