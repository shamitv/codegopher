# Fixture Projects

These projects are tiny, deterministic inputs for CodeGopher tests. Tests that mutate files must copy a fixture into a temporary directory first and leave the tracked fixture source unchanged.

Each fixture README names the behavior it is intended to exercise.

Use `basic_python_package` for read/list/glob/grep coverage, `buggy_cli_app` for shell and agent diagnostics, `configured_project` for config and ignore-file behavior, and `edit_safety_project` for prior-read and write safety tests.
