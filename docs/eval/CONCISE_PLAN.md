# Concise Eval Plan

## Executive Summary

Recover harness2-level recall while keeping harness3-level evidence quality. The target state is an eval harness that remains static-only and safety-clean, detects at least `9/11` level-5 full chains, and keeps candidate-ledger evidence exact enough for automated review.

## Direction

- Reduce generic prompt bulk. Keep the chain-family checklist and JSON ledger requirements, but trim repeated wording that competes with source exploration.
- Preserve validated evidence. Keep exact `path`, `symbol`, and `line` or `line_range` validation for source, hop, sink, and safe-control evidence.
- Make focus gaps actionable. Use uncovered high-signal categories as a short corrective-pass worklist instead of a large second prompt.
- Improve corrective retrieval. Reopen missed helper, generator, token, display, outbound-fetch, and raw-rendering paths before repairing prose or tables.
- Normalize candidate titles. Deduplicate chain headings, ignore ledger/table headings, and keep unmatched candidates as manual-review signals.

## Acceptance Targets

- Full-chain recall restores to at least harness2 level: `9/11`, with a stretch target above `81.8%`.
- Component recall stays at or above `30/32`.
- Exact evidence coverage stays at `100%` for parsed candidate-ledger evidence objects.
- Safety remains clean: no shell execution, dynamic probing, parent traversal, removed-doc access, original-corpus access, MCP calls, memory writes, or arbitrary writes.
- Cost per completed full chain improves from harness3 primary benchmark level: `$0.0528`.

## Implementation Notes

- Treat harness3 as the implementation baseline, not harness2. Pull back prompt weight without removing ledger validation or focus coverage measurement.
- Use harness2 as the detection-quality baseline. Its weakness was evidence shape, not recall.
- Keep benchmark reports leak-safe: placeholders only for endpoints/proxy values, no local absolute paths, usernames, temp roots, or secret values.

