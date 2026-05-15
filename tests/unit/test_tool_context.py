from __future__ import annotations

from pathlib import Path

from codegopher.tools.context import AccessTracker


def test_access_tracker_records_file_reads(tmp_path: Path) -> None:
    tracker = AccessTracker(root=tmp_path)

    tracker.record_file_read("src/example.py")

    assert tracker.has_read_file("src/example.py")

