"""Report writers for development-only benchmark runs."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ReportMetadata:
    title: str
    report_root: Path
    temp_root: Path
    endpoint: str
    model: str
    api_family: str
    previous_report: Path | None = None
    proxy_run_url: str | None = None


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2), encoding="utf-8")


def write_markdown(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def render_app_analysis(summary: dict[str, Any]) -> str:
    lines = [
        f"# Analysis - {summary['display_name']}",
        "",
        f"- App key: `{summary['app']}`",
        f"- Temp workspace: `{summary['workspace']}`",
        f"- Return code: {summary['returncode']}",
        f"- Attempts: {summary['attempt_count']}",
        f"- Generated report: {'yes' if summary['generated_report_exists'] else 'no'}",
        f"- Report writer called: {'yes' if summary['write_report_called'] else 'no'}",
        "",
        "## Event Counts",
        "",
        "| Event | Count |",
        "|---|---:|",
    ]
    for event_type, count in summary["event_counts"].items():
        lines.append(f"| `{event_type}` | {count} |")
    lines.extend(["", "## Safety", ""])
    safety = summary["safety"]
    lines.extend(
        [
            f"- Compromised run: {'yes' if safety['compromised'] else 'no'}",
            f"- Removed docs referenced in tool calls: {', '.join(safety['removed_doc_refs_in_tool_calls']) or 'none'}",
            f"- Parent/original-root refs in tool calls: {', '.join(safety['parent_or_absolute_refs_in_tool_calls']) or 'none'}",
            f"- Unsafe tool calls: {len(safety['unsafe_tool_calls'])}",
            f"- Denied or unknown tool results: {len(safety['denied_or_unknown_tool_results'])}",
            f"- Output mentions removed docs: {'yes' if safety['mentions_removed_docs_in_output'] else 'no'}",
            f"- Output mentions original root: {'yes' if safety['mentions_original_root_in_output'] else 'no'}",
        ]
    )
    lines.extend(["", "## Ground Truth Recall", ""])
    ground_truth = summary["ground_truth"]
    lines.extend(
        [
            f"- Status: {ground_truth['status']}",
            f"- Components detected: {ground_truth['detected_components']} / {ground_truth['total_components']}",
            f"- Recall: {ground_truth['recall']:.3f}",
            f"- Full chains: {ground_truth.get('full_chains', 0)} / {ground_truth.get('total_chains', 0)}",
            f"- Full-chain recall: {ground_truth.get('full_chain_recall', 0.0):.3f}",
            "",
        ]
    )
    _append_group_summary(lines, "Recall By Difficulty", ground_truth.get("by_difficulty", {}))
    _append_group_summary(lines, "Recall By Family", ground_truth.get("by_family", {}))
    for chain in ground_truth["chains"]:
        lines.extend(
            [
                f"### {chain['chain_name']}",
                "",
                f"- Status: {chain['status']}",
                f"- Difficulty: {chain.get('difficulty', 'medium')}",
                f"- Vulnerability family: {chain.get('vulnerability_family', 'unspecified')}",
                f"- Components detected: {chain['detected_components']} / {chain['total_components']}",
                f"- Missing required evidence: {', '.join(chain.get('missing_required_evidence', [])) or 'none'}",
                f"- Decoy misfires: {', '.join(chain.get('decoy_misfires', [])) or 'none'}",
                "",
                "| Step | Method | Location | Detected | Evidence Terms | Required Hits | Missing Required | Negative Hits |",
                "|---|---|---|---|---|---|---|---|",
            ]
        )
        for component in chain["components"]:
            lines.append(
                "| {step} | `{method}` | `{location}` | {detected} | {terms} | {required_hits} | {missing} | {negative} |".format(
                    step=component["step"],
                    method=component["method"],
                    location=component["location"],
                    detected="yes" if component["detected"] else "no",
                    terms=", ".join(component["description_term_hits"]) or "none",
                    required_hits=", ".join(component.get("required_evidence_hits", [])) or "none",
                    missing=", ".join(component.get("missing_required_evidence", [])) or "none",
                    negative=", ".join(component.get("negative_evidence_hits", [])) or "none",
                )
            )
        lines.append("")
    quality = summary["report_quality"]
    lines.extend(
        [
            "## Report Quality",
            "",
            f"- Line reference count: {quality['line_reference_count']}",
            f"- Ground-truth components with location and method cited: {quality['components_with_location_and_method']} / {quality['total_components']}",
            f"- Unmatched candidate chain titles: {', '.join(quality['unmatched_candidate_chain_titles']) or 'none'}",
            f"- Decoy misfire count: {quality.get('decoy_misfire_count', 0)}",
            "",
            "## Tool Calls",
            "",
        ]
    )
    for call in summary["tool_calls"]:
        lines.append(
            f"- `{call.get('tool_name')}` `{call.get('tool_id')}` {call.get('arguments_summary', '')}"
        )
    if not summary["tool_calls"]:
        lines.append("- None")
    return "\n".join(lines)


def render_aggregate_report(
    *,
    metadata: ReportMetadata,
    summaries: list[dict[str, Any]],
    command: list[str],
) -> str:
    lines = [
        f"# {metadata.title}",
        "",
        f"- Created: {datetime.now().isoformat(timespec='seconds')}",
        f"- Report root: `{metadata.report_root}`",
        f"- Temp root: `{metadata.temp_root}`",
        f"- LLM endpoint: `{metadata.endpoint}`",
        f"- Model: `{metadata.model}`",
        f"- API family: `{metadata.api_family}`",
        "- Scope: development-only benchmark tooling; no public `cgopher benchmark` command.",
    ]
    if metadata.previous_report:
        lines.append(f"- Previous report: `{metadata.previous_report}`")
    if metadata.proxy_run_url:
        lines.append(f"- Proxy run page: `{metadata.proxy_run_url}`")
    lines.extend(
        [
            "",
            "## Command Shape",
            "",
            "```powershell",
            " ".join(_quote_arg(part) for part in command),
            "```",
            "",
            "## Results",
            "",
            "## Recall By Difficulty",
            "",
        ]
    )
    _append_aggregate_group_summary(lines, summaries, "by_difficulty")
    lines.extend(["", "## Recall By Vulnerability Family", ""])
    _append_aggregate_group_summary(lines, summaries, "by_family")
    lines.extend(
        [
            "",
            "## Per-App Results",
            "",
            "| App | Report Generated | Writer Called | Recall Status | Chains | Components | Safety Compromised | Hygiene Passed | Line Refs | Missing Evidence | Decoy Misfires | Unmatched Candidates | Attempts |",
            "|---|---|---|---|---:|---:|---|---|---:|---:|---:|---:|---:|",
        ]
    )
    for summary in summaries:
        ground_truth = summary["ground_truth"]
        quality = summary["report_quality"]
        missing_evidence = sum(
            len(chain.get("missing_required_evidence", []))
            for chain in ground_truth.get("chains", [])
        )
        decoy_misfires = sum(
            len(chain.get("decoy_misfires", []))
            for chain in ground_truth.get("chains", [])
        )
        lines.append(
            "| {app} | {report} | {writer} | {status} | {chains} | {components} | {safety} | {hygiene} | {line_refs} | {missing} | {decoys} | {unmatched} | {attempts} |".format(
                app=summary["app"],
                report="yes" if summary["generated_report_exists"] else "no",
                writer="yes" if summary["write_report_called"] else "no",
                status=ground_truth["status"],
                chains=f"{ground_truth.get('full_chains', 0)}/{ground_truth.get('total_chains', 0)}",
                components=f"{ground_truth['detected_components']}/{ground_truth['total_components']}",
                safety="yes" if summary["safety"]["compromised"] else "no",
                hygiene="yes" if summary.get("hygiene", {}).get("passed") else "no",
                line_refs=quality["line_reference_count"],
                missing=missing_evidence,
                decoys=decoy_misfires,
                unmatched=len(quality["unmatched_candidate_chain_titles"]),
                attempts=summary["attempt_count"],
            )
        )
    _append_baseline_comparison(lines, metadata.previous_report, summaries)
    lines.extend(["", "## Outcome", ""])
    if summaries and all(summary["ground_truth"]["status"] == "full" for summary in summaries):
        lines.append("- All planted ground-truth chains were fully detected.")
    else:
        lines.append("- One or more planted ground-truth chains were only partially detected or missed.")
    if summaries and all(not summary["safety"]["compromised"] for summary in summaries):
        lines.append("- No removed-doc, original-root, or parent-path tool access was observed.")
    else:
        lines.append("- One or more runs showed isolation concerns; inspect per-app analysis.")
    if summaries and all(summary.get("hygiene", {}).get("passed") for summary in summaries):
        lines.append("- Hygiene checks passed for all sanitized temp workspaces.")
    else:
        lines.append("- One or more hygiene checks had residual hints; inspect hygiene artifacts.")
    lines.extend(
        [
            "- Unmatched candidate chains are reported for manual review and are not treated as false positives unless the manifest is exhaustive.",
            "",
            "## Artifact Index",
            "",
            "- `ground_truth/*.md`: evaluator-only manifest summaries.",
            "- `logs/*.events.jsonl`: raw CodeGopher event streams.",
            "- `logs/*.stderr.log`: process stderr.",
            "- `outputs/*.generated_report.md`: generated chained audit reports or missing-report notes.",
            "- `outputs/*.final_text.md`: final assistant text.",
            "- `analysis/*.analysis.md`: per-app human analysis.",
            "- `analysis/*.summary.json`: machine-readable per-app summaries.",
            "- `hygiene/*.hygiene.md`: removed-file and sanitized-source hint reports.",
            "- `hygiene/*.hygiene.json`: machine-readable hygiene reports.",
        ]
    )
    return "\n".join(lines)


def _quote_arg(value: str) -> str:
    if not value or any(char.isspace() for char in value) or '"' in value:
        return '"' + value.replace('"', '`"') + '"'
    return value


def _append_group_summary(lines: list[str], title: str, groups: dict[str, object]) -> None:
    if not groups:
        return
    lines.extend([f"## {title}", "", "| Group | Chains | Components |", "|---|---:|---:|"])
    for name, raw in groups.items():
        if not isinstance(raw, dict):
            continue
        lines.append(
            "| {name} | {chains} | {components} |".format(
                name=name,
                chains=f"{raw.get('full_chains', 0)}/{raw.get('total_chains', 0)}",
                components=f"{raw.get('detected_components', 0)}/{raw.get('total_components', 0)}",
            )
        )
    lines.append("")


def _append_aggregate_group_summary(
    lines: list[str],
    summaries: list[dict[str, Any]],
    key: str,
) -> None:
    totals: dict[str, dict[str, int]] = {}
    for summary in summaries:
        groups = summary.get("ground_truth", {}).get(key, {})
        if not isinstance(groups, dict):
            continue
        for name, raw in groups.items():
            if not isinstance(raw, dict):
                continue
            total = totals.setdefault(
                str(name),
                {
                    "full_chains": 0,
                    "total_chains": 0,
                    "detected_components": 0,
                    "total_components": 0,
                },
            )
            for metric in total:
                total[metric] += int(raw.get(metric, 0))
    if not totals:
        lines.append("- No grouped recall data available.")
        return
    lines.extend(["| Group | Chains | Components |", "|---|---:|---:|"])
    for name, total in sorted(totals.items()):
        lines.append(
            "| {name} | {chains} | {components} |".format(
                name=name,
                chains=f"{total['full_chains']}/{total['total_chains']}",
                components=f"{total['detected_components']}/{total['total_components']}",
            )
        )


def _append_baseline_comparison(
    lines: list[str],
    previous_report: Path | None,
    summaries: list[dict[str, Any]],
) -> None:
    if previous_report is None:
        return
    previous = _load_previous_summaries(previous_report)
    lines.extend(["", "## Baseline Comparison", ""])
    if not previous:
        lines.append("- Previous summary JSON files were not found or could not be parsed.")
        return
    lines.extend(
        [
            "| App | Previous Recall | Sanitized Recall | Previous Safety | Sanitized Safety | Previous Line Refs | Sanitized Line Refs |",
            "|---|---|---|---|---|---:|---:|",
        ]
    )
    current_by_app = {summary["app"]: summary for summary in summaries}
    for app, current in current_by_app.items():
        prior = previous.get(app, {})
        lines.append(
            "| {app} | {previous_recall} | {current_recall} | {previous_safety} | {current_safety} | {previous_refs} | {current_refs} |".format(
                app=app,
                previous_recall=_recall_label(prior),
                current_recall=_recall_label(current),
                previous_safety=_safety_label(prior),
                current_safety=_safety_label(current),
                previous_refs=prior.get("report_quality", {}).get("line_reference_count", "n/a"),
                current_refs=current.get("report_quality", {}).get("line_reference_count", "n/a"),
            )
        )


def _load_previous_summaries(previous_report: Path) -> dict[str, dict[str, Any]]:
    analysis_dir = previous_report.parent / "analysis"
    if not analysis_dir.is_dir():
        return {}
    summaries: dict[str, dict[str, Any]] = {}
    for path in analysis_dir.glob("*.summary.json"):
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(value, dict) and isinstance(value.get("app"), str):
            summaries[value["app"]] = value
    return summaries


def _recall_label(summary: dict[str, Any]) -> str:
    ground_truth = summary.get("ground_truth", {})
    if not isinstance(ground_truth, dict):
        return "n/a"
    status = ground_truth.get("status", "n/a")
    detected = ground_truth.get("detected_components", "n/a")
    total = ground_truth.get("total_components", "n/a")
    return f"{status} ({detected}/{total})"


def _safety_label(summary: dict[str, Any]) -> str:
    safety = summary.get("safety", {})
    if not isinstance(safety, dict):
        return "n/a"
    return "compromised" if safety.get("compromised") else "clean"
