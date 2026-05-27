"""Development-only benchmark harness for chained vulnerability audits."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from codegopher.devtools.benchmark.coverage import (
    discovery_quality_to_dict,
    evaluate_discovery_quality,
    evaluate_focus_coverage,
    focus_coverage_to_dict,
)
from codegopher.devtools.benchmark.evaluator import (
    count_line_references,
    evaluate_ground_truth,
    evaluate_report_quality,
    evaluate_safety,
    evaluation_to_dict,
    parse_candidate_chain_ledger,
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
from codegopher.devtools.benchmark.prepass import (
    SOURCE_FAMILY_DISCOVERY_ORDER,
    StaticFocusQueue,
    build_static_focus_queue,
    render_static_focus_queue,
)
from codegopher.devtools.benchmark.reporter import (
    ReportMetadata,
    render_aggregate_report,
    render_app_analysis,
    write_json,
    write_markdown,
)
from codegopher.security.report import DEFAULT_CHAINED_VULNERABILITY_REPORT

BASE_BENCHMARK_PROMPT = (
    "Use @skill:chained-vulnerability-static-audit to perform a static-only chained "
    "vulnerability review of this codebase. Inspect only the current working directory. "
    "Do not use live probes, dynamic scanners, shell commands, hidden evaluator "
    "metadata, dotfiles, or files outside this workspace. Write the final report with "
    "write_chained_vulnerability_report to docs/security/CHAINED_VULNERABILITIES_REVIEW.md."
)
CHAIN_FAMILY_CHECKLIST = """
Use this generic chain-family checklist; do not assume any item exists unless source evidence supports it:

- Cross-file authorization or tenant confusion: user-controlled identifier -> missing ownership/tenant check -> privileged read/write.
- Query or expression construction: request input -> query/filter/string builder -> data disclosure or unauthorized mutation.
- SSRF/open redirect/internal fetch: URL or callback input -> normalization/redirect bypass -> internal resource, metadata, or privileged callback sink.
- Reset, invite, session, or token chain: predictable or reusable token -> trust boundary hop -> account/session takeover or privilege change.
- Identifier/reference/display helper chain: generated or predictable ID -> lookup endpoint -> raw or sensitive display sink.
- Crypto/key/fallback misuse: weak or reused secret -> legacy compatibility path -> forged token, plaintext exposure, or integrity bypass.
- Deserialization/template/path/archive flow: import/render/path input -> parser or filesystem hop -> code/data exposure or overwrite.
- Race/state/background-job confusion: state-changing endpoint -> queued job/webhook/delayed transition -> unauthorized final state.
- Error/config exposure chain: verbose error/config leak -> secret/internal identifier discovery -> follow-on privileged action.

Report requirements:

- Include a section titled "Candidate Chain Ledger".
- Include a fenced JSON block with a top-level `candidate_chains` array.
- Each JSON candidate must include `status`, `family`, `source`, `hop`, `sink`, `safe_controls`, `confidence`, and `missing_evidence`.
- `source`, `hop`, `sink`, and `safe_controls` entries must use evidence objects with full repo-relative `path`, exact `symbol`, and `line` or `line_range`.
- Every safe control must include `classification` with exactly one of `same_path_blocker`, `nearby_only`, `not_applicable`, or `unknown`.
- For every candidate chain, include source, hop, sink, file, symbol, line or line range, confidence, missing evidence, and safe control/decoy rejection.
- Use `read_file` with `include_line_numbers=true` when gathering final evidence.
- Cite code evidence as `relative/path.ext:line` or `relative/path.ext:line-line`.
- Use full repository-relative paths and exact method/symbol names in every final evidence row. Do not abbreviate citations to `File.java:line` when the full path is known.
- If no complete chain is provable, still call the report writer and include reviewed areas, rejected candidates, missing evidence, and incomplete chains.
""".strip()
CORRECTIVE_BENCHMARK_PROMPT = """
Continue the same static-only chained vulnerability review. The current audit is missing one or more generic quality gates: line-numbered evidence, a Candidate Chain Ledger, or a clear complete-chain/incomplete-chain conclusion.

Do not use hidden manifests, removed evaluator files, dotfiles, parent directories, live probes, dynamic scanners, shell commands, or files outside this workspace.

Use only source-derived evidence. Re-read the minimum necessary source files with `read_file` and `include_line_numbers=true`, then update the final report with `write_chained_vulnerability_report` to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`.

Every final evidence row must cite the full repository-relative path, exact symbol or method name, and line or line range. Replace abbreviated citations such as `Controller.java:40-47` with full citations such as `src/main/java/example/Controller.java:40-47`.

Also include or repair the fenced JSON candidate ledger with a top-level `candidate_chains` array. Every `source`, `hop`, `sink`, and `safe_controls` evidence object must include `path`, `symbol`, and `line` or `line_range`.

Every safe control must include a `classification` value from exactly this set: `same_path_blocker`, `nearby_only`, `not_applicable`, `unknown`. Use `nearby_only` when the guard is present but does not block the exact candidate path.

Before finishing, perform these generic sweeps and record each result in the Candidate Chain Ledger:

- source-controlled identifiers plus missing ownership or tenant checks
- quiet helper prerequisites such as ID/token/reference generators, display helpers, summaries, and raw-label builders
- query/filter/string-builder sinks
- outbound fetch, redirect, webhook, or callback flows
- reset/invite/session/token trust transitions
- crypto/key fallback or legacy compatibility paths
- template/deserialization/path/archive flows
- race/state/background-job or delayed webhook sinks
- verbose error or config exposure that can enable a follow-on action

For each candidate, state whether it is complete, incomplete, or rejected because a safe control blocks it. Include file, symbol, line/range, confidence, missing evidence, and decoy/safe-control rejection rows.
""".strip()
REDACTED_PROMPT_FOR_REPORT = "<structured chained-audit benchmark prompt via events stdin>"
MAX_CORRECTIVE_FOCUS_ITEMS = 16


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
    structured_prepass: bool = True
    corrective_second_pass: bool = True


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
        self._focus_queues: dict[str, StaticFocusQueue] = {}

    def run(self) -> BenchmarkRunResult:
        self._ensure_dirs()
        summaries = []
        for case in self.config.cases:
            print(f"[{_now()}] Preparing {case.key}", flush=True)
            summary = self.run_case(case)
            summaries.append(summary)
            print(f"[{_now()}] Completed {case.key}", flush=True)
        command = self._build_command() if self.config.cases else []
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
        prepass = self._build_prepass(case, workspace)
        prompt = self._build_benchmark_prompt(prepass)
        attempts = self._run_with_retry(case, workspace, prompt)
        corrective_used = False
        initial_events = parse_events(attempts[-1].stdout)
        initial_tool_calls = [
            event for event in initial_events if event.get("type") == "tool_call"
        ]
        focus_queue = self._focus_queues.get(case.key)
        corrective_reasons = self._corrective_reasons(
            workspace,
            prepass,
            focus_queue,
            initial_tool_calls,
        )
        if self.config.corrective_second_pass and corrective_reasons:
            print(f"[{_now()}] Running corrective pass for {case.key}", flush=True)
            corrective_used = True
            corrective_prompt = self._build_corrective_prompt(
                workspace,
                corrective_reasons,
                focus_queue,
                initial_tool_calls,
            )
            corrective = self._run_process(
                case,
                workspace,
                len(attempts) + 1,
                corrective_prompt,
            )
            attempts.append(corrective)
            self._write_attempt_logs(case, corrective)
        final = attempts[-1]
        self._write_text(self.output_dir / "logs" / f"{case.key}.events.jsonl", final.stdout)
        self._write_text(self.output_dir / "logs" / f"{case.key}.stderr.log", final.stderr)
        summary = self._analyze(
            case,
            manifest,
            workspace,
            attempts,
            corrective_used=corrective_used,
            corrective_reasons=corrective_reasons,
        )
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

    def _run_with_retry(
        self,
        case: BenchmarkCase,
        workspace: Path,
        prompt: str,
    ) -> list[ProcessAttempt]:
        attempts = []
        max_attempts = self.config.retries + 1
        for attempt_number in range(1, max_attempts + 1):
            attempt = self._run_process(case, workspace, attempt_number, prompt)
            attempts.append(attempt)
            self._write_attempt_logs(case, attempt)
            if not _should_retry(attempt):
                break
            print(f"[{_now()}] Retrying transient failure for {case.key}", flush=True)
        return attempts

    def _run_process(
        self,
        case: BenchmarkCase,
        workspace: Path,
        attempt: int,
        prompt: str,
    ) -> ProcessAttempt:
        command = tuple(self._build_command())
        input_text = _events_stdin_prompt(
            prompt=prompt,
            workspace=workspace,
            turn_id=f"benchmark-{case.key}-attempt-{attempt}",
        )
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
                input=input_text,
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

    def _build_command(self) -> list[str]:
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
        return command

    def _build_prepass(self, case: BenchmarkCase, workspace: Path) -> str:
        if not self.config.structured_prepass:
            return ""
        queue = build_static_focus_queue(workspace)
        self._focus_queues[case.key] = queue
        prepass = render_static_focus_queue(queue)
        self._write_text(self.output_dir / "analysis" / f"{case.key}.prepass.md", prepass)
        return prepass

    def _build_benchmark_prompt(self, prepass: str) -> str:
        sections = [BASE_BENCHMARK_PROMPT, CHAIN_FAMILY_CHECKLIST]
        if prepass:
            sections.append(prepass)
        return "\n\n".join(sections)

    def _write_attempt_logs(self, case: BenchmarkCase, attempt: ProcessAttempt) -> None:
        self._write_text(
            self.output_dir / "logs" / f"{case.key}.attempt{attempt.attempt}.events.jsonl",
            attempt.stdout,
        )
        self._write_text(
            self.output_dir / "logs" / f"{case.key}.attempt{attempt.attempt}.stderr.log",
            attempt.stderr,
        )

    def _needs_corrective_pass(self, workspace: Path, prepass: str = "") -> bool:
        return bool(self._corrective_reasons(workspace, prepass, None, []))

    def _build_corrective_prompt(
        self,
        workspace: Path,
        reasons: tuple[str, ...],
        focus_queue: StaticFocusQueue | None,
        tool_calls: list[dict[str, Any]] | None,
    ) -> str:
        sections = [CORRECTIVE_BENCHMARK_PROMPT]
        discovery_guidance = self._render_missing_source_family_worklist(
            workspace,
            focus_queue,
            tool_calls,
        )
        if discovery_guidance:
            sections.append(discovery_guidance)
        if reasons:
            sections.append(
                "Quality gate failures to repair:\n"
                + "\n".join(f"- {reason}" for reason in reasons[:12])
            )
        focus_guidance = self._render_uncovered_focus_worklist(
            workspace,
            focus_queue,
            tool_calls,
        )
        if focus_guidance:
            sections.append(focus_guidance)
        return "\n\n".join(sections)

    def _render_missing_source_family_worklist(
        self,
        workspace: Path,
        focus_queue: StaticFocusQueue | None,
        tool_calls: list[dict[str, Any]] | None,
    ) -> str:
        if focus_queue is None:
            return ""
        report = self._read_workspace_report(workspace)
        discovery = evaluate_discovery_quality(
            focus_queue,
            tool_calls=tool_calls or [],
            report_text=report,
        )
        repair_families = (
            *discovery.missing_high_risk_families,
            *discovery.weak_high_risk_families,
        )
        repair_families = tuple(sorted(set(repair_families), key=_source_family_order))
        if not repair_families:
            return ""
        lines = [
            "Discovery repair worklist:",
            "- Before polishing the report, re-read representative files from these unreviewed or under-reviewed high-risk source families.",
            "- If no complete chain is still provable after this review, say discovery is incomplete rather than presenting a completed no-chain result.",
        ]
        item_count = 0
        for family in repair_families:
            family_label = next(
                (
                    item.label
                    for item in discovery.source_families
                    if item.family == family
                ),
                family,
            )
            covered_paths = next(
                (
                    family_coverage.covered_paths
                    for family_coverage in discovery.source_families
                    if family_coverage.family == family
                ),
                (),
            )
            uncovered = sorted(
                [
                    item
                    for category in focus_queue.categories
                    for item in category.items
                    if item.source_family == family
                    and item.path not in covered_paths
                ],
                key=lambda item: (
                    -_corrective_item_score(item),
                    item.path,
                    item.line,
                    item.snippet,
                ),
            )
            unique_uncovered: list[Any] = []
            seen_paths: set[str] = set()
            for item in uncovered:
                if item.path in seen_paths:
                    continue
                seen_paths.add(item.path)
                unique_uncovered.append(item)
            uncovered = unique_uncovered[:5]
            if not uncovered:
                continue
            lines.append(f"- {family_label}:")
            for item in uncovered:
                lines.append(f"  - {item.item_id} `{item.path}:{item.line}` {item.snippet}")
                item_count += 1
                if item_count >= MAX_CORRECTIVE_FOCUS_ITEMS:
                    return "\n".join(lines)
        return "\n".join(lines) if item_count else ""

    def _render_uncovered_focus_worklist(
        self,
        workspace: Path,
        focus_queue: StaticFocusQueue | None,
        tool_calls: list[dict[str, Any]] | None,
    ) -> str:
        if focus_queue is None:
            return ""
        report = self._read_workspace_report(workspace)
        coverage = evaluate_focus_coverage(
            focus_queue,
            tool_calls=tool_calls or [],
            report_text=report,
        )
        if not coverage.high_signal_uncovered_categories:
            return ""
        covered_paths_by_category = {
            category.category: set(category.covered_paths)
            for category in coverage.categories
        }
        lines = [
            "Targeted uncovered focus worklist:",
            "- Re-read only the minimum source files needed to close these source-only coverage gaps.",
            "- Do not restart the whole audit; repair chain consistency and evidence for these items.",
        ]
        item_count = 0
        for category_name in coverage.high_signal_uncovered_categories:
            queue_category = next(
                (
                    category
                    for category in focus_queue.categories
                    if category.name == category_name
                ),
                None,
            )
            if queue_category is None:
                continue
            covered_paths = covered_paths_by_category.get(category_name, set())
            uncovered = [
                item
                for item in queue_category.items
                if item.path not in covered_paths
            ][:4]
            if not uncovered:
                continue
            lines.append(f"- {category_name}:")
            for item in uncovered:
                lines.append(f"  - {item.item_id} `{item.path}:{item.line}` {item.snippet}")
                item_count += 1
                if item_count >= MAX_CORRECTIVE_FOCUS_ITEMS:
                    return "\n".join(lines)
        return "\n".join(lines) if item_count else ""

    def _corrective_reasons(
        self,
        workspace: Path,
        prepass: str = "",
        focus_queue: StaticFocusQueue | None = None,
        tool_calls: list[dict[str, Any]] | None = None,
    ) -> tuple[str, ...]:
        report = self._read_workspace_report(workspace)
        if not report:
            return ()
        report_l = report.lower()
        ledger = parse_candidate_chain_ledger(report)
        reasons: list[str] = []
        has_ledger = "candidate chain ledger" in report_l
        has_json_ledger = bool(ledger["present"])
        has_line_refs = count_line_references(report) > 0
        claims_no_complete_chain = any(
            marker in report_l
            for marker in (
                "no complete chains",
                "no chains detected",
                "complete chains detected: 0",
                "chain count: 0",
            )
        )
        claims_complete_chain = any(
            marker in report_l
            for marker in (
                "status: complete",
                "complete chain",
                "confirmed chain",
                "full chain",
                "| complete",
                "| **complete**",
            )
        )
        has_unresolved_completeness_marker = any(
            marker in report_l
            for marker in (
                "no audit of",
                "not reviewed",
                "not fully reviewed",
                "missing proof",
                "missing required",
                "missing prerequisite",
                "not provably connected",
                "not fully proven",
                "unresolved evidence",
            )
        )
        has_exact_evidence_gap = _has_abbreviated_code_refs(report) or (
            has_json_ledger
            and ledger["total_evidence_items"] > 0
            and ledger["exact_evidence_items"] < ledger["total_evidence_items"]
        )
        has_missing_json_ledger = not has_json_ledger
        has_helper_omission = _prepass_has_helper_items(prepass) and _omits_helper_review(
            report
        )
        has_nearby_guard_over_rejection = _has_nearby_guard_over_rejection(report, ledger)
        has_unknown_safe_controls = _has_only_unknown_safe_controls(ledger)
        has_contradiction = _has_contradictory_conclusions(report)
        focus_coverage = evaluate_focus_coverage(
            focus_queue,
            tool_calls=tool_calls or [],
            report_text=report,
        )
        discovery_quality = evaluate_discovery_quality(
            focus_queue,
            tool_calls=tool_calls or [],
            report_text=report,
        )
        if has_missing_json_ledger:
            reasons.append("missing JSON candidate ledger")
        if ledger.get("validation_errors"):
            reasons.extend(str(error) for error in ledger["validation_errors"])
        if not has_ledger:
            reasons.append("missing Candidate Chain Ledger section")
        if not has_line_refs:
            reasons.append("missing line-numbered evidence")
        if claims_no_complete_chain and not claims_complete_chain:
            reasons.append("claims no complete chain without reviewed complete candidates")
        if claims_no_complete_chain and not discovery_quality.discovery_complete:
            repair_families = (
                *discovery_quality.missing_high_risk_families,
                *discovery_quality.weak_high_risk_families,
            )
            repair_families = tuple(
                sorted(set(repair_families), key=_source_family_order)
            )
            missing = ", ".join(repair_families[:6])
            reasons.append(f"no-chain conclusion before discovery coverage: {missing}")
        if claims_complete_chain and has_unresolved_completeness_marker:
            reasons.append("complete-chain claim has unresolved evidence markers")
        if has_ledger and has_exact_evidence_gap:
            reasons.append("ledger has incomplete exact path/symbol/line evidence")
        if has_helper_omission:
            reasons.append("helper/generator focus items were not discussed")
        if has_nearby_guard_over_rejection:
            reasons.append("nearby-only safe control appears to reject a chain")
        if has_unknown_safe_controls:
            reasons.append("safe controls lack specific classifications")
        if has_contradiction:
            reasons.append("report has contradictory complete/incomplete conclusions")
        for category in focus_coverage.high_signal_uncovered_categories:
            reasons.append(f"high-signal focus category was not reviewed: {category}")
        return tuple(dict.fromkeys(reasons))

    def _analyze(
        self,
        case: BenchmarkCase,
        manifest: VulnerabilityManifest,
        workspace: Path,
        attempts: list[ProcessAttempt],
        *,
        corrective_used: bool,
        corrective_reasons: tuple[str, ...],
    ) -> dict[str, Any]:
        final = attempts[-1]
        final_events = parse_events(final.stdout)
        all_events = [
            event
            for attempt in attempts
            for event in parse_events(attempt.stdout)
        ]
        tool_calls = [event for event in all_events if event.get("type") == "tool_call"]
        tool_results = [event for event in all_events if event.get("type") == "tool_result"]
        final_text = final_text_from_events(final_events)
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
        focus_coverage = evaluate_focus_coverage(
            self._focus_queues.get(case.key),
            tool_calls=tool_calls,
            report_text=generated_report + "\n" + final_text,
        )
        discovery_quality = evaluate_discovery_quality(
            self._focus_queues.get(case.key),
            tool_calls=tool_calls,
            report_text=generated_report + "\n" + final_text,
        )
        return {
            "app": case.key,
            "display_name": case.display_name,
            "workspace": str(workspace),
            "returncode": final.returncode,
            "command": list(final.command),
            "attempt_count": len(attempts),
            "corrective_pass_used": corrective_used,
            "corrective_reasons": list(corrective_reasons),
            "corrective_reason_categories": _corrective_reason_categories(
                corrective_reasons
            ),
            "event_counts": event_counts(all_events),
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
            "focus_coverage": focus_coverage_to_dict(focus_coverage),
            "discovery_quality": discovery_quality_to_dict(discovery_quality),
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

    def _read_workspace_report(self, workspace: Path) -> str:
        output_report = workspace / DEFAULT_CHAINED_VULNERABILITY_REPORT
        if not output_report.exists():
            return ""
        return output_report.read_text(encoding="utf-8", errors="replace")

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


def _events_stdin_prompt(*, prompt: str, workspace: Path, turn_id: str) -> str:
    start_turn = {
        "version": 1,
        "type": "start_turn",
        "turn_id": turn_id,
        "workspace_root": str(workspace),
        "prompt": prompt,
    }
    shutdown = {"version": 1, "type": "shutdown"}
    return json.dumps(start_turn) + "\n" + json.dumps(shutdown) + "\n"


def _has_abbreviated_code_refs(report: str) -> bool:
    file_line = re.compile(
        r"(?<![\w./\\-])([\w./\\-]+\.(?:py|ts|tsx|js|jsx|java|html|css)):\d+\b",
        flags=re.IGNORECASE,
    )
    for match in file_line.finditer(report):
        path = match.group(1)
        if "/" not in path and "\\" not in path:
            return True
    return False


def _source_family_order(family: str) -> tuple[int, str]:
    try:
        return (SOURCE_FAMILY_DISCOVERY_ORDER.index(family), family)
    except ValueError:
        return (len(SOURCE_FAMILY_DISCOVERY_ORDER), family)


def _corrective_reason_categories(reasons: tuple[str, ...]) -> dict[str, int]:
    categories = {"discovery": 0, "report_format": 0, "safety": 0, "other": 0}
    for reason in reasons:
        reason_l = reason.lower()
        if any(
            marker in reason_l
            for marker in (
                "discovery",
                "focus category",
                "focus item",
                "coverage",
            )
        ):
            categories["discovery"] += 1
        elif any(
            marker in reason_l
            for marker in (
                "ledger",
                "evidence",
                "line-number",
                "contradictory",
                "safe control",
                "complete-chain claim",
            )
        ):
            categories["report_format"] += 1
        elif any(marker in reason_l for marker in ("unsafe", "removed", "parent")):
            categories["safety"] += 1
        else:
            categories["other"] += 1
    return categories


def _corrective_item_score(item: Any) -> int:
    category_bonus = {
        "Routes and entry points": 35,
        "State-changing and privileged sinks": 30,
        "Auth and authorization controls": 25,
        "Query, LDAP, and expression sinks": 20,
        "Outbound fetch and SSRF surfaces": 20,
        "Rendering and raw HTML sinks": 20,
        "Safe controls and possible decoys": 15,
        "Verbose errors and config exposure": 10,
    }.get(str(getattr(item, "category", "")), 0)
    path = str(getattr(item, "path", "")).lower()
    snippet = str(getattr(item, "snippet", "")).lower()
    family = str(getattr(item, "source_family", ""))
    combined = f"{path} {snippet}"
    priority = getattr(item, "priority", 0)
    score = int(priority) + category_bonus
    if "/static/" in path and family not in {"static_js_sink", "static_html_signal"}:
        score -= 25
    if "health" in combined:
        score -= 45
    high_signal_terms = (
        "admin",
        "auth",
        "bulk",
        "callback",
        "create",
        "delete",
        "flag",
        "login",
        "product",
        "report",
        "secret",
        "session",
        "settings",
        "supplier",
        "update",
        "upload",
        "user",
        "validator",
        "webhook",
    )
    if any(term in combined for term in high_signal_terms):
        score += 25
    if "settings.py" in path or "secret_key" in combined:
        score += 30
    if "add_url_rule" in combined:
        score += 15
    if "def " in combined or snippet.strip().startswith("@"):
        score += 10
    return score


def _prepass_has_helper_items(prepass: str) -> bool:
    if "### Identifier, token, reference, and display helpers" not in prepass:
        return False
    section = prepass.split("### Identifier, token, reference, and display helpers", 1)[1]
    section = section.split("\n### ", 1)[0]
    return "FQ" in section


def _omits_helper_review(report: str) -> bool:
    report_l = report.lower()
    helper_terms = (
        "generator",
        "generate",
        "token",
        "reference",
        "identifier",
        "display helper",
        "summary",
        "raw label",
        "pnr",
    )
    return not any(term in report_l for term in helper_terms)


def _has_nearby_guard_over_rejection(report: str, ledger: dict[str, Any]) -> bool:
    counts = ledger.get("safe_control_counts", {})
    nearby_count = counts.get("nearby_only", 0) if isinstance(counts, dict) else 0
    report_l = report.lower()
    text_marker = "nearby" in report_l and any(
        marker in report_l for marker in ("reject", "rejected", "blocks", "blocked")
    )
    return bool(nearby_count and text_marker)


def _has_only_unknown_safe_controls(ledger: dict[str, Any]) -> bool:
    counts = ledger.get("safe_control_counts", {})
    if not isinstance(counts, dict):
        return False
    total = sum(count for count in counts.values() if isinstance(count, int))
    unknown = counts.get("unknown", 0)
    return bool(total and unknown == total)


def _has_contradictory_conclusions(report: str) -> bool:
    report_l = report.lower()
    complete_markers = ("complete chain", "confirmed chain", "status: complete", "| complete")
    incomplete_markers = (
        "same chain is incomplete",
        "also incomplete",
        "not fully proven",
        "partially inferred",
        "not provably connected",
    )
    return any(marker in report_l for marker in complete_markers) and any(
        marker in report_l for marker in incomplete_markers
    )
