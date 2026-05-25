# v0.8 Development Chained Vulnerability Benchmark Report

- Created: 2026-05-24T23:40:41
- Report root: `D:\work\codegopher\docs\plans\v0.8\report\20260524-233650`
- Temp root: `C:\Users\shamit\AppData\Local\Temp\codegopher-v08-chain-20260524-233650`
- LLM endpoint: `http://192.168.96.5:8080/v1`
- Model: `Qwen/Qwen3.6-35B-A3B`
- API family: `chat_completions`
- Scope: development-only benchmark tooling; no public `cgopher benchmark` command.
- Previous report: `D:\work\codegopher\docs\plans\v0.8\report\20260524-105121\REPORT.md`

## Command Shape

```powershell
D:\work\codegopher\.venv\Scripts\cgopher.exe --events --no-project-init --approval-mode yolo --model Qwen/Qwen3.6-35B-A3B --base-url http://192.168.96.5:8080/v1 --api-family chat_completions --replay-reasoning-content -p "Use @skill:chained-vulnerability-static-audit to perform a static-only chained vulnerability review of this codebase. Inspect only the current working directory. Do not use live probes, dynamic scanners, shell commands, or files outside this workspace. Write the final report with write_chained_vulnerability_report to docs/security/CHAINED_VULNERABILITIES_REVIEW.md."
```

## Results

| App | Report Generated | Writer Called | Recall Status | Components | Safety Compromised | Hygiene Passed | Line Refs | Unmatched Candidates | Attempts |
|---|---|---|---|---:|---|---|---:|---:|---:|
| app-02-patient-portal | yes | yes | full | 3/3 | no | yes | 2 | 0 | 1 |
| app-07-airline-booking | yes | yes | full | 3/3 | no | yes | 19 | 5 | 1 |
| app-12-crypto-wallet | yes | yes | full | 3/3 | no | yes | 2 | 2 | 1 |

## Baseline Comparison

| App | Previous Recall | Sanitized Recall | Previous Safety | Sanitized Safety | Previous Line Refs | Sanitized Line Refs |
|---|---|---|---|---|---:|---:|
| app-02-patient-portal | full (3/3) | full (3/3) | clean | clean | 37 | 2 |
| app-07-airline-booking | full (3/3) | full (3/3) | clean | clean | 22 | 19 |
| app-12-crypto-wallet | full (3/3) | full (3/3) | clean | clean | 19 | 2 |

## Outcome

- All planted ground-truth chains were fully detected.
- No removed-doc, original-root, or parent-path tool access was observed.
- Hygiene checks passed for all sanitized temp workspaces.
- Unmatched candidate chains are reported for manual review and are not treated as false positives unless the manifest is exhaustive.

## Artifact Index

- `ground_truth/*.md`: evaluator-only manifest summaries.
- `logs/*.events.jsonl`: raw CodeGopher event streams.
- `logs/*.stderr.log`: process stderr.
- `outputs/*.generated_report.md`: generated chained audit reports or missing-report notes.
- `outputs/*.final_text.md`: final assistant text.
- `analysis/*.analysis.md`: per-app human analysis.
- `analysis/*.summary.json`: machine-readable per-app summaries.
- `hygiene/*.hygiene.md`: removed-file and sanitized-source hint reports.
- `hygiene/*.hygiene.json`: machine-readable hygiene reports.
