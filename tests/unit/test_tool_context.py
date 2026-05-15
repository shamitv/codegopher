from __future__ import annotations

from pathlib import Path

import pytest

from codegopher.core.errors import ToolExecutionError
from codegopher.tools.context import AccessTracker


def test_access_tracker_records_file_reads(tmp_path: Path) -> None:
    tracker = AccessTracker(root=tmp_path)

    tracker.record_file_read("src/example.py")

    assert tracker.has_read_file("src/example.py")


def test_access_tracker_records_directory_inspections(tmp_path: Path) -> None:
    tracker = AccessTracker(root=tmp_path)

    tracker.record_directory_inspection("src")

    assert tracker.has_inspected_directory("src")


def test_access_tracker_allows_existing_file_edit_after_read(tmp_path: Path) -> None:
    tracker = AccessTracker(root=tmp_path)
    tracker.record_file_read("src/example.py")

    tracker.require_prior_read("src/example.py")


def test_access_tracker_rejects_existing_file_edit_without_read(tmp_path: Path) -> None:
    tracker = AccessTracker(root=tmp_path)

    with pytest.raises(ToolExecutionError, match="must read it first"):
        tracker.require_prior_read("src/example.py")


def test_access_tracker_allows_new_file_after_parent_inspection(tmp_path: Path) -> None:
    tracker = AccessTracker(root=tmp_path)
    tracker.record_directory_inspection("src")

    tracker.require_parent_inspection("src/new.py")


def test_access_tracker_rejects_new_file_without_parent_inspection(tmp_path: Path) -> None:
    tracker = AccessTracker(root=tmp_path)

    with pytest.raises(ToolExecutionError, match="list_dir must inspect parent directory"):
        tracker.require_parent_inspection("src/new.py")
