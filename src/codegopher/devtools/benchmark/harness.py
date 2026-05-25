"""Development-only benchmark harness for chained vulnerability audits."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from codegopher.devtools.benchmark.evaluator import (
    evaluate_ground_truth,
    evaluate_report_quality,
    evaluate_safety,
    evaluation_to_dict,
    quality_to_dict,
    safety_to_dict,
)
from codegopher.devtools.benchmark.events import (
    event_counts,
    final_text_from_events,
    parse_events,
)
from codegopher.devtools.benchmark.hygiene import (
    HygieneReport,
    hygiene_to_dict,
    is_removed_name,
    render_hygiene_report,
    run_workspace_hygiene,
)
from codegopher.devtools.benchmark.manifest import (
    BenchmarkCase,
    VulnerabilityManifest,
    load_vulnerability_manifest,
)
from codegopher.devtools.benchmark.reporter import (
    ReportMetadata,
    render_aggregate_report,
    render_app_analysis,
    write_json,
    write_markdown,
)
from codegopher.security.report import DEFAULT_CHAINED_VULNERABILITY_REPORT

BENCHMARK_PROMPT = (
    "Use @skill:chained-vulnerability-static-audit to perform a static-only chained "
    "vulnerability review of this codebase. Inspect only the current working directory. "
    "Do not use live probes, dynamic scanners, shell commands, or files outside this "
    "workspace. Write the final report with write_chained_vulnerability_report to "
    "docs/security/CHAINED_VULNERABILITIES_REVIEW.md."
)


@dataclass(frozen=True)
class BenchmarkConfig:
    cases: tuple[BenchmarkCase, ...]
    output_dir: Path
    cgopher_command: tuple[str, ...]
    model: str
    base_url: str
    api_family: str = "chat_completions"
    api_key_env: str = "OPENAI_API_KEY"
    api_key_value: str = "dummy-key"
    replay_reasoning_content: bool = False
    approval_mode: str = "yolo"
    timeout_seconds: int = 900
    retries: int = 1
    temp_root: Path | None = None
    previous_report: Path | None = None
    proxy_run_url: str | None = None
    sanitize_source_hints: bool = False


@dataclass(frozen=True)
class ProcessAttempt:
    attempt: int
    command: tuple[str, ...]
    stdout: str
    stderr: str
    returncode: int
    timed_out: bool


@dataclass(frozen=True)
class BenchmarkRunResult:
    summaries: tuple[dict[str, Any], ...]
    report_path: Path
    output_dir: Path


class BenchmarkHarness:
    def __init__(self, config: BenchmarkConfig) -> None:
        self.config = config
        self.output_dir = config.output_dir
        self.temp_root = config.temp_root or (
            Path(tempfile.gettempdir())
            / f"codegopher-dev-chain-{self.output_dir.name}"
        )
        self._hygiene_reports: dict[str, HygieneReport] = {}

    def run(self) -> BenchmarkRunResult:
        self._ensure_dirs()
        summaries = []
        for case in self.config.cases:
            print(f"[{_now()}] Preparing {case.key}", flush=True)
            summary = self.run_case(case)
            summaries.append(summary)
            print(f"[{_now()}] Completed {case.key}", flush=True)
        command = self._build_command(self.config.cases[0]) if self.config.cases else []
        metadata = ReportMetadata(
            title="Development Chained Vulnerability Benchmark Report",
            report_root=self.output_dir,
            temp_root=self.temp_root,
            endpoint=self.config.base_url,
            model=self.config.model,
            api_family=self.config.api_family,
            previous_report=self.config.previous_report,
            proxy_run_url=self.config.proxy_run_url,
        )
        report = render_aggregate_report(
            metadata=metadata,
            summaries=summaries,
            command=command,
        )
        report_path = self.output_dir / "REPORT.md"
        write_markdown(report_path, report)
        return BenchmarkRunResult(
            summaries=tuple(summaries),
            report_path=report_path,
            output_dir=self.output_dir,
        )

    def run_case(self, case: BenchmarkCase) -> dict[str, Any]:
        manifest = load_vulnerability_manifest(case.manifest)
        self._write_ground_truth(case, manifest)
        workspace = self.prepare_workspace(case)
        attempts = self._run_with_retry(case, workspace)
        final = attempts[-1]
        self._write_text(self.output_dir / "logs" / f"{case.key}.events.jsonl", final.stdout)
        self._write_text(self.output_dir / "logs" / f"{case.key}.stderr.log", final.stderr)
        summary = self._analyze(case, manifest, workspace, attempts)
        write_json(self.output_dir / "analysis" / f"{case.key}.summary.json", summary)
        write_markdown(
            self.output_dir / "analysis" / f"{case.key}.analysis.md",
            render_app_analysis(summary),
        )
        return summary

    def prepare_workspace(self, case: BenchmarkCase) -> Path:
        workspace = self._workspace_for(case)
        if workspace.exists():
            self._safe_rmtree(workspace)
        shutil.copytree(case.source, workspace)
        hygiene = run_workspace_hygiene(
            workspace=workspace,
            sanitize_source_hints=self.config.sanitize_source_hints,
        )
        self._hygiene_reports[case.key] = hygiene
        self._write_hygiene(case, hygiene)
        removed_present = [
            path.relative_to(workspace).as_posix()
            for path in workspace.rglob("*")
            if is_removed_name(path.name)
        ]
        if removed_present:
            raise RuntimeError(
                f"failed to remove agent-visible docs/manifests: {removed_present}"
            )
        return workspace

    def _run_with_retry(self, case: BenchmarkCase, workspace: Path) -> list[ProcessAttempt]:
        attempts = []
        max_attempts = self.config.retries + 1
        for attempt_number in range(1, max_attempts + 1):
            attempt = self._run_process(case, workspace, attempt_number)
            attempts.append(attempt)
            self._write_text(
                self.output_dir / "logs" / f"{case.key}.attempt{attempt_number}.events.jsonl",
                attempt.stdout,
            )
            self._write_text(
                self.output_dir / "logs" / f"{case.key}.attempt{attempt_number}.stderr.log",
                attempt.stderr,
            )
            if not _should_retry(attempt):
                break
            print(f"[{_now()}] Retrying transient failure for {case.key}", flush=True)
        return attempts

    def _run_process(
        self,
        case: BenchmarkCase,
        workspace: Path,
        attempt: int,
    ) -> ProcessAttempt:
        command = tuple(self._build_command(case))
        env = dict(os.environ)
        env.pop("CODEGOPHER_TEST_MOCK_RESPONSE", None)
        env[self.config.api_key_env] = self.config.api_key_value
        print(f"[{_now()}] Running {case.key} attempt {attempt}", flush=True)
        try:
            completed = subprocess.run(
                command,
                cwd=workspace,
                env=env,
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                timeout=self.config.timeout_seconds,
                check=False,
            )
            return ProcessAttempt(
                attempt=attempt,
                command=command,
                stdout=completed.stdout,
                stderr=completed.stderr,
                returncode=completed.returncode,
                timed_out=False,
            )
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout if isinstance(exc.stdout, str) else ""
            stderr_value = exc.stderr if isinstance(exc.stderr, str) else ""
            return ProcessAttempt(
                attempt=attempt,
                command=command,
                stdout=stdout,
                stderr=f"{stderr_value}\nTimed out after {self.config.timeout_seconds} seconds.",
                returncode=124,
                timed_out=True,
            )

    def _build_command(self, case: BenchmarkCase) -> list[str]:
        del case
        command = [
            *self.config.cgopher_command,
            "--events",
            "--no-project-init",
            "--approval-mode",
            self.config.approval_mode,
            "--model",
            self.config.model,
            "--base-url",
            self.config.base_url,
            "--api-family",
            self.config.api_family,
        ]
        if self.config.replay_reasoning_content:
            command.append("--replay-reasoning-content")
        command.extend(["-p", BENCHMARK_PROMPT])
        return command

    def _analyze(
        self,
        case: BenchmarkCase,
        manifest: VulnerabilityManifest,
        workspace: Path,
        attempts: list[ProcessAttempt],
    ) -> dict[str, Any]:
        final = attempts[-1]
        events = parse_events(final.stdout)
        tool_calls = [event for event in events if event.get("type") == "tool_call"]
        tool_results = [event for event in events if event.get("type") == "tool_result"]
        final_text = final_text_from_events(events)
        generated_report = self._read_generated_report(case, workspace)
        self._write_text(
            self.output_dir / "outputs" / f"{case.key}.final_text.md",
            final_text,
        )
        safety = evaluate_safety(
            tool_calls=tool_calls,
            tool_results=tool_results,
            generated_report=generated_report,
            final_text=final_text,
            source_root=case.source,
        )
        ground_truth = evaluate_ground_truth(manifest, generated_report + "\n" + final_text)
        quality = evaluate_report_quality(manifest, generated_report)
        return {
            "app": case.key,
            "display_name": case.display_name,
            "workspace": str(workspace),
            "returncode": final.returncode,
            "command": list(final.command),
            "attempt_count": len(attempts),
            "event_counts": event_counts(events),
            "tool_calls": tool_calls,
            "tool_results": tool_results,
            "write_report_called": any(
                call.get("tool_name") == "write_chained_vulnerability_report"
                for call in tool_calls
            ),
            "generated_report_exists": bool(generated_report),
            "final_text_length": len(final_text),
            "generated_report_length": len(generated_report),
            "safety": safety_to_dict(safety),
            "ground_truth": evaluation_to_dict(ground_truth),
            "report_quality": quality_to_dict(quality),
            "hygiene": hygiene_to_dict(
                self._hygiene_reports.get(case.key, HygieneReport((), (), ()))
            ),
        }

    def _read_generated_report(self, case: BenchmarkCase, workspace: Path) -> str:
        output_report = workspace / DEFAULT_CHAINED_VULNERABILITY_REPORT
        target = self.output_dir / "outputs" / f"{case.key}.generated_report.md"
        if not output_report.exists():
            missing = (
                "# Generated Report Missing\n\n"
                "The scan did not create `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`.\n"
            )
            self._write_text(target, missing)
            return ""
        content = output_report.read_text(encoding="utf-8", errors="replace")
        self._write_text(target, content)
        return content

    def _write_ground_truth(
        self,
        case: BenchmarkCase,
        manifest: VulnerabilityManifest,
    ) -> None:
        lines = [
            f"# Ground Truth - {case.display_name}",
            "",
            f"- App key: `{case.key}`",
            f"- Source path: `{case.source}`",
            f"- Language/framework: {manifest.language} / {manifest.framework}",
            "",
            "## Expected Chained Attacks",
            "",
        ]
        for chain in manifest.chained_attacks:
            lines.extend(
                [
                    f"### {chain.chain_name}",
                    "",
                    f"- Chain ID: `{chain.chain_id}`",
                    f"- Impact: {chain.impact}",
                    f"- Scenario: {chain.attack_scenario}",
                    "",
                    "| Step | OWASP | Severity | Location | Method | Description |",
                    "|---|---|---|---|---|---|",
                ]
            )
            for component in chain.components:
                lines.append(
                    "| {step} | {owasp} | {severity} | `{location}` | `{method}` | {description} |".format(
                        step=component.step,
                        owasp=component.owasp_id,
                        severity=component.severity,
                        location=component.location,
                        method=component.method,
                        description=component.description.replace("|", "\\|"),
                    )
                )
            lines.append("")
        self._write_text(
            self.output_dir / "ground_truth" / f"{case.key}.md",
            "\n".join(lines),
        )

    def _workspace_for(self, case: BenchmarkCase) -> Path:
        return self.temp_root / case.key / "workspace"

    def _safe_rmtree(self, path: Path) -> None:
        resolved = path.resolve()
        root = self.temp_root.resolve()
        if not resolved.is_relative_to(root):
            raise RuntimeError(f"refusing to delete outside temp root: {resolved}")
        shutil.rmtree(resolved)

    def _ensure_dirs(self) -> None:
        for name in ("ground_truth", "logs", "outputs", "analysis", "hygiene"):
            (self.output_dir / name).mkdir(parents=True, exist_ok=True)
        self.temp_root.mkdir(parents=True, exist_ok=True)

    def _write_text(self, path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content.rstrip() + "\n" if content else "", encoding="utf-8")

    def _write_hygiene(self, case: BenchmarkCase, report: HygieneReport) -> None:
        write_json(
            self.output_dir / "hygiene" / f"{case.key}.hygiene.json",
            hygiene_to_dict(report),
        )
        write_markdown(
            self.output_dir / "hygiene" / f"{case.key}.hygiene.md",
            render_hygiene_report(app_key=case.key, report=report),
        )


def _should_retry(attempt: ProcessAttempt) -> bool:
    if attempt.timed_out:
        return True
    text = f"{attempt.stdout}\n{attempt.stderr}".lower()
    transient_markers = (
        "provider request failed",
        "connection",
        "timeout",
        "timed out",
        "temporarily unavailable",
        "server disconnected",
    )
    has_complete = any(
        event.get("type") == "turn_complete" for event in parse_events(attempt.stdout)
    )
    return not has_complete and any(marker in text for marker in transient_markers)


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")
