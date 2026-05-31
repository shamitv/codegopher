# CodeGopher v0.16 Plan: Local Qwen Cache Stability

## Summary

v0.16 is a local-Qwen-focused quality slice. It stabilizes the repeated prompt prefix, exposes output-token control for long report-writer calls, and adds one-command focused validation automation for the local Responses model.

This slice does not add a public benchmark command, does not run GPT validation, and does not start the seven-app validation.

## Goals

- Improve prompt-cache reuse by keeping stable system prompt sections before volatile turn state.
- Reduce local report-writer truncation risk by allowing larger provider output budgets.
- Keep local Qwen validation reproducible with a small internal script.
- Preserve static-only audit boundaries and sanitized reporting.

## Implementation Scope

- Reorder `build_system_prompt` so stable content appears first:
  - core instructions
  - tool list
  - loaded skills
  - selected memories
  - runtime episode memory
  - TODOs
  - mission contract
- Add `CODEGOPHER_MAX_OUTPUT_TOKENS` and `--max-output-tokens` support for the main CLI.
- Add internal benchmark `--max-output-tokens` and pass it through to spawned `cgopher`.
- Update benchmark prompts to ask local and slow Responses models for concise, evidence-dense final reports before calling the report writer.
- Add `scripts/run_v016_local_qwen_focused.sh` for local Qwen focused validation on sanitized `app-05`, `app-10`, and `app-14`.

## Validation Scope

Run only local `Qwen 3.5 35B` on the focused subset:

- `app-05`
- `app-10`
- `app-14`

The script uses sanitized source hints, a one-hour per-app timeout, and a larger output-token budget for the local model.

## Baseline

Compare the focused rerun against the v0.15 local Qwen baseline:

- Components: `17/19`
- Complete chains: `6/8`
- Valid ledgers: `2/3`
- Writer completion: `3/3`
- Known local issues: malformed tool-call attempts on `app-05` and `app-14`, cache misses during repeated large prompts, and output-budget pressure around report writing.

## Success Criteria

- Focused recall does not regress from the v0.15 local Qwen baseline.
- Report writer completion remains `3/3`.
- Valid ledgers do not regress.
- Malformed report-writer calls reduce, or the remaining blocker is clearly diagnosed.
- Prompt-cache reuse improves when proxy stats expose cached input, or the remaining cache blocker is documented.
- Committed docs contain only sanitized aggregate observations.

## Out Of Scope

- GPT reruns.
- Full seven-app validation.
- Public benchmark commands.
- Cost or wall-time optimization beyond the local timeout and output-budget settings.
- Chunked or fallback report writing; large single-call report payloads remain a known local-model risk.
- Server-side tuning for the local model runtime.

## Redaction Policy

Do not commit raw logs, proxy snapshots, generated reports, temp roots, endpoint values, local usernames, original corpus paths, or secret names/values. Validation docs should include only sanitized aggregate conclusions.
