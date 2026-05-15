from __future__ import annotations

from pathlib import Path

from codegopher.tools.fs.ignore import IgnoreMatcher


def test_ignore_matcher_reads_patterns(tmp_path: Path) -> None:
    (tmp_path / ".codegopherignore").write_text("ignored/\n*.secret\n", encoding="utf-8")
    (tmp_path / "ignored").mkdir()
    ignored = tmp_path / "ignored" / "file.txt"
    ignored.write_text("", encoding="utf-8")
    secret = tmp_path / "local.secret"
    secret.write_text("", encoding="utf-8")

    matcher = IgnoreMatcher.from_file(tmp_path)

    assert matcher.matches(ignored, tmp_path)
    assert matcher.matches(secret, tmp_path)


def test_ignore_matcher_does_not_crash_for_paths_outside_root(tmp_path: Path) -> None:
    matcher = IgnoreMatcher.from_file(tmp_path)

    assert matcher.matches(tmp_path.parent / "outside.txt", tmp_path) is False
