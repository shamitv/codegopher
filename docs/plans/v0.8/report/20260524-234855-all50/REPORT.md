# v0.8 Development Chained Vulnerability Benchmark Report

- Created: 2026-05-25T01:03:24
- Report root: `D:\work\codegopher\docs\plans\v0.8\report\20260524-234855-all50`
- Temp root: `C:\Users\shamit\AppData\Local\Temp\codegopher-v08-chain-20260524-234855-all50`
- LLM endpoint: `http://192.168.96.5:8080/v1`
- Model: `Qwen/Qwen3.6-35B-A3B`
- API family: `chat_completions`
- Scope: development-only benchmark tooling; no public `cgopher benchmark` command.

## Command Shape

```powershell
D:\work\codegopher\.venv\Scripts\cgopher.exe --events --no-project-init --approval-mode yolo --model Qwen/Qwen3.6-35B-A3B --base-url http://192.168.96.5:8080/v1 --api-family chat_completions --replay-reasoning-content -p "Use @skill:chained-vulnerability-static-audit to perform a static-only chained vulnerability review of this codebase. Inspect only the current working directory. Do not use live probes, dynamic scanners, shell commands, or files outside this workspace. Write the final report with write_chained_vulnerability_report to docs/security/CHAINED_VULNERABILITIES_REVIEW.md."
```

## Results

| App | Report Generated | Writer Called | Recall Status | Components | Safety Compromised | Hygiene Passed | Line Refs | Unmatched Candidates | Attempts |
|---|---|---|---|---:|---|---|---:|---:|---:|
| app-01-ecommerce-catalog | yes | yes | full | 3/3 | no | yes | 42 | 3 | 1 |
| app-02-patient-portal | yes | yes | full | 3/3 | no | yes | 0 | 6 | 1 |
| app-03-banking-service | yes | yes | full | 3/3 | no | yes | 4 | 3 | 1 |
| app-04-real-estate | yes | yes | full | 3/3 | no | yes | 13 | 0 | 1 |
| app-05-learning-mgmt | yes | yes | full | 2/2 | no | yes | 19 | 0 | 1 |
| app-06-hr-management | yes | yes | full | 3/3 | no | yes | 9 | 3 | 1 |
| app-07-airline-booking | yes | yes | full | 3/3 | no | yes | 24 | 4 | 2 |
| app-08-warehouse-mgmt | yes | yes | full | 3/3 | no | yes | 20 | 3 | 2 |
| app-09-legal-documents | yes | yes | full | 2/2 | no | yes | 7 | 2 | 1 |
| app-10-telecom-billing | yes | yes | full | 3/3 | no | yes | 29 | 5 | 1 |
| app-11-social-analytics | yes | yes | full | 3/3 | no | yes | 13 | 2 | 1 |
| app-12-crypto-wallet | yes | yes | full | 3/3 | no | yes | 2 | 5 | 1 |
| app-13-project-mgmt | yes | yes | full | 3/3 | no | yes | 19 | 1 | 1 |
| app-14-telemedicine | yes | yes | full | 2/2 | no | yes | 13 | 3 | 1 |
| app-15-digital-assets | yes | yes | full | 2/2 | no | yes | 19 | 4 | 1 |
| app-16-restaurant-reviews | yes | yes | full | 2/2 | no | yes | 15 | 3 | 1 |
| app-17-iot-dashboard | yes | yes | full | 2/2 | no | yes | 19 | 5 | 1 |
| app-18-p2p-lending | yes | yes | full | 2/2 | no | yes | 16 | 4 | 1 |
| app-19-cms | yes | yes | full | 2/2 | no | yes | 21 | 3 | 1 |
| app-20-fitness-tracker | yes | yes | full | 2/2 | no | yes | 21 | 4 | 1 |
| app-21-insurance-claims | yes | yes | full | 3/3 | no | yes | 34 | 0 | 1 |
| app-22-food-delivery | yes | yes | full | 2/2 | no | yes | 28 | 1 | 1 |
| app-23-govt-permits | no | no | missed | 0/2 | no | yes | 0 | 0 | 1 |
| app-24-vet-clinic | yes | yes | full | 3/3 | no | yes | 19 | 3 | 1 |
| app-25-supply-chain | yes | yes | full | 2/2 | no | yes | 17 | 1 | 1 |
| app-26-pharma-tracking | yes | yes | full | 2/2 | no | yes | 9 | 0 | 1 |
| app-27-hotel-reservation | yes | yes | full | 2/2 | no | yes | 6 | 3 | 1 |
| app-28-mfg-quality | yes | yes | full | 3/3 | no | yes | 21 | 1 | 1 |
| app-29-fleet-management | yes | yes | full | 2/2 | no | yes | 2 | 4 | 1 |
| app-30-auction-platform | yes | yes | full | 2/2 | no | yes | 13 | 2 | 1 |
| app-31-event-ticketing | yes | yes | full | 2/2 | no | yes | 2 | 5 | 1 |
| app-32-support-tickets | yes | yes | full | 2/2 | no | yes | 19 | 4 | 1 |
| app-33-recruitment-ats | yes | yes | full | 2/2 | no | yes | 18 | 5 | 1 |
| app-34-subscription-box | yes | yes | full | 2/2 | no | yes | 0 | 5 | 1 |
| app-35-compliance-tracker | yes | yes | full | 2/2 | no | yes | 14 | 3 | 1 |
| app-36-parking-mgmt | yes | yes | full | 2/2 | no | yes | 27 | 3 | 1 |
| app-37-crop-planner | yes | yes | full | 2/2 | no | yes | 0 | 3 | 1 |
| app-38-museum-catalog | yes | yes | full | 2/2 | no | yes | 22 | 1 | 1 |
| app-39-wedding-planner | yes | yes | full | 2/2 | no | yes | 0 | 3 | 1 |
| app-40-pet-adoption | yes | yes | full | 2/2 | no | yes | 5 | 2 | 1 |
| app-41-library-reservation | yes | yes | full | 2/2 | no | yes | 10 | 3 | 1 |
| app-42-construction-tracker | yes | yes | full | 2/2 | no | yes | 42 | 5 | 1 |
| app-43-music-streaming | no | no | missed | 0/2 | no | yes | 0 | 0 | 2 |
| app-44-election-polling | yes | yes | full | 2/2 | no | yes | 0 | 5 | 1 |
| app-45-travel-expense | yes | yes | full | 2/2 | no | yes | 22 | 3 | 1 |
| app-46-charity-donations | yes | yes | full | 3/3 | no | yes | 7 | 9 | 1 |
| app-47-smart-home | yes | yes | full | 3/3 | no | yes | 16 | 0 | 1 |
| app-48-freelancer-market | yes | yes | full | 2/2 | no | yes | 0 | 3 | 2 |
| app-49-sports-league | no | no | missed | 0/3 | no | yes | 0 | 0 | 1 |
| app-50-energy-billing | yes | yes | full | 2/2 | no | yes | 0 | 2 | 1 |

## Outcome

- One or more planted ground-truth chains were only partially detected or missed.
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
