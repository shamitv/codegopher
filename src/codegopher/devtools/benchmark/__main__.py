"""CLI entry point for development-only benchmark runs."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from codegopher.devtools.benchmark.harness import BenchmarkConfig, BenchmarkHarness
from codegopher.devtools.benchmark.manifest import (
    BenchmarkCase,
    load_benchmark_suite,
    parse_app_spec,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run development-only chained vulnerability benchmarks.",
    )
    parser.add_argument("--suite", type=Path, help="TOML suite containing [[apps]] entries.")
    parser.add_argument(
        "--app",
        action="append",
        default=[],
        help="App spec: KEY|DISPLAY_NAME|SOURCE_PATH|MANIFEST_PATH. May be repeated.",
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--cgopher", required=True, help="Path to cgopher executable.")
    parser.add_argument(
        "--cgopher-arg",
        action="append",
        default=[],
        help="Additional command prefix argument before CodeGopher flags. For tests only.",
    )
    parser.add_argument("--model", required=True)
    parser.add_argument("--base-url", required=True)
    parser.add_argument(
        "--api-family",
        choices=("chat_completions", "responses"),
        default="chat_completions",
    )
    parser.add_argument("--api-key-env", default="OPENAI_API_KEY")
    parser.add_argument("--api-key-value", default="dummy-key")
    parser.add_argument("--replay-reasoning-content", action="store_true")
    parser.add_argument("--timeout-seconds", type=int, default=900)
    parser.add_argument("--retries", type=int, default=1)
    parser.add_argument("--temp-root", type=Path)
    parser.add_argument("--previous-report", type=Path)
    parser.add_argument("--proxy-run-url")
    parser.add_argument("--sanitize-source-hints", action="store_true")
    parser.add_argument(
        "--no-structured-prepass",
        action="store_true",
        help="Disable the source-derived inventory prompt section.",
    )
    parser.add_argument(
        "--no-corrective-second-pass",
        action="store_true",
        help="Disable the generic quality-gate corrective pass.",
    )
    args = parser.parse_args(argv)

    cases = _cases_from_args(args.suite, args.app)
    config = BenchmarkConfig(
        cases=cases,
        output_dir=args.output_dir,
        cgopher_command=(args.cgopher, *args.cgopher_arg),
        model=args.model,
        base_url=args.base_url,
        api_family=args.api_family,
        api_key_env=args.api_key_env,
        api_key_value=args.api_key_value,
        replay_reasoning_content=args.replay_reasoning_content,
        timeout_seconds=args.timeout_seconds,
        retries=args.retries,
        temp_root=args.temp_root,
        previous_report=args.previous_report,
        proxy_run_url=args.proxy_run_url,
        sanitize_source_hints=args.sanitize_source_hints,
        structured_prepass=not args.no_structured_prepass,
        corrective_second_pass=not args.no_corrective_second_pass,
    )
    result = BenchmarkHarness(config).run()
    print(f"Wrote {result.report_path}")
    return 0


def _cases_from_args(suite: Path | None, app_specs: list[str]) -> tuple[BenchmarkCase, ...]:
    cases: list[BenchmarkCase] = []
    if suite is not None:
        cases.extend(load_benchmark_suite(suite))
    cases.extend(parse_app_spec(spec) for spec in app_specs)
    if not cases:
        raise SystemExit("pass --suite or at least one --app")
    return tuple(cases)


if __name__ == "__main__":
    sys.exit(main())
