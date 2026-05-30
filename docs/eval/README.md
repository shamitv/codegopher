## Executive Summary

The current chained-vulnerability eval implementation is useful for analyst-assisted review, but it is not yet reliable enough for unattended "all chains found" claims. The strongest invariant across the recent runs is safety: the benchmark harness consistently preserved static-only isolation, generated sanitized temp workspaces, and avoided unsafe tool use. The implementation has also improved report structure, especially line-numbered evidence, candidate ledgers, and exact path/symbol/line validation.

The timeline is not a straight-line improvement. The early Responses baseline proved execution safety but had weak recall. Structured and follow-up runs improved evidence quality and two-app recall. Harness2 produced the best observed detection result on the nine level-5 apps: `9/11` full chains and `30/32` components. Harness3 is the current implementation direction and produced much cleaner validated evidence, `117/117` exact evidence objects, but regressed to `7/11` full chains and cost more per completed chain.

The next eval work should preserve harness3's evidence validation while recovering harness2-level vulnerability finding. In practice, that means reducing prompt bulk, using uncovered focus gaps more selectively, improving corrective-pass retrieval, and normalizing candidate titles without distracting the model from source coverage.

## Navigation

| Document | Purpose |
|---|---|
| [CONCISE_PLAN.md](CONCISE_PLAN.md) | Short forward plan for the next eval implementation pass. |
| [CURRENT_STATE_REFERENCE.md](CURRENT_STATE_REFERENCE.md) | Detailed timeline-style reference for current eval behavior, results, costs, and detected vulnerability families. |

## Source Reports

The docs in this folder summarize committed benchmark reports under `docs/plans/v0.10/report/`. Raw event logs, temp workspaces, proxy snapshots, and local endpoint values remain outside `docs/eval`.

