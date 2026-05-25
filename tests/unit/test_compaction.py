from __future__ import annotations

from pathlib import Path

from codegopher.core.compaction import (
    build_compaction_prompt,
    compacted_messages,
    split_for_compaction,
)
from codegopher.core.types import Message


def sample_messages() -> list[Message]:
    return [
        {"role": "user", "content": "first goal"},
        {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "call-1",
                    "type": "function",
                    "function": {"name": "read_file", "arguments": '{"path":"README.md"}'},
                }
            ],
        },
        {"role": "tool", "tool_call_id": "call-1", "content": "readme contents"},
        {"role": "assistant", "content": "found the notes"},
        {"role": "user", "content": "second goal"},
        {"role": "assistant", "content": "second answer"},
        {"role": "user", "content": "third goal"},
    ]


def test_split_for_compaction_keeps_recent_user_turns() -> None:
    split = split_for_compaction(sample_messages(), preserve_recent_user_turns=2)

    assert split.older_messages[0]["content"] == "first goal"
    assert split.older_messages[-1]["content"] == "found the notes"
    assert split.recent_messages[0] == {"role": "user", "content": "second goal"}
    assert split.recent_messages[-1] == {"role": "user", "content": "third goal"}


def test_split_for_compaction_keeps_all_messages_when_history_is_short() -> None:
    messages = [{"role": "user", "content": "only goal"}]

    split = split_for_compaction(messages)

    assert split.older_messages == []
    assert split.recent_messages == messages


def test_build_compaction_prompt_includes_older_messages_and_tool_context(
    tmp_path: Path,
) -> None:
    prompt = build_compaction_prompt(sample_messages(), cwd=tmp_path)

    assert "Older messages to summarize" in prompt
    assert "first goal" in prompt
    assert "read_file" in prompt
    assert "readme contents" in prompt
    assert "Recent messages to preserve verbatim" in prompt
    assert "second goal" in prompt


def test_build_compaction_prompt_includes_manual_instructions(tmp_path: Path) -> None:
    prompt = build_compaction_prompt(
        sample_messages(),
        cwd=tmp_path,
        instructions="focus on file decisions",
    )

    assert "User compaction instructions" in prompt
    assert "focus on file decisions" in prompt


def test_build_compaction_prompt_includes_todo_memory_and_skill_context(
    tmp_path: Path,
) -> None:
    prompt = build_compaction_prompt(
        sample_messages(),
        cwd=tmp_path,
        todo_items=["finish parser tests"],
        memories=["Project uses pytest"],
        skills=["python-testing: prefer focused tests"],
    )

    assert "Active TODO state" in prompt
    assert "finish parser tests" in prompt
    assert "Selected memories" in prompt
    assert "Project uses pytest" in prompt
    assert "Loaded skills" in prompt
    assert "python-testing" in prompt


def test_build_compaction_prompt_includes_mission_context(tmp_path: Path) -> None:
    prompt = build_compaction_prompt(
        sample_messages(),
        cwd=tmp_path,
        mission_items=["Mission: Chained audit", "Required artifacts: report.md"],
    )

    assert "Active mission contract and task ledger" in prompt
    assert "Mission: Chained audit" in prompt


def test_compacted_messages_preserves_recent_turns_verbatim() -> None:
    messages: list[Message] = [
        {"role": "user", "content": "old question"},
        {"role": "assistant", "content": "old answer"},
        {"role": "user", "content": "recent question"},
        {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "call-2",
                    "type": "function",
                    "function": {"name": "read_file", "arguments": '{"path":"x.py"}'},
                }
            ],
        },
        {"role": "tool", "tool_call_id": "call-2", "content": "file body"},
        {"role": "assistant", "content": "recent answer"},
        {"role": "user", "content": "latest question"},
    ]

    compacted = compacted_messages(
        messages,
        summary="summary text",
        reason="manual",
        instructions="keep files",
        preserve_recent_user_turns=2,
    )

    assert compacted[0]["role"] == "system"
    assert "summary text" in str(compacted[0]["content"])
    assert "keep files" in str(compacted[0]["content"])
    assert compacted[1:] == messages[2:]
    assert messages[0] not in compacted
