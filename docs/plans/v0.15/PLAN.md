# CodeGopher v0.15 Plan - Recall Recovery And Candidate-Flow Repair

## Background

The v0.14 focused validation showed a stable source-driven workflow when the
model can inspect the workspace, but the results still stopped short of the
best observed recall from earlier runs. The successful path was consistent:
start with workspace inventory, expand into family-specific source discovery,
update TODO state while collecting evidence, and write a chained-vulnerability
report only after enough source support is available.

What worked best:

- broad source-family sweeps from entry points into services, repositories,
  config, and workers/consumers
- explicit TODO updates to preserve candidate evidence and repair progress
- report-writing after concrete source evidence was gathered
- corrective re-reads when a high-signal category was still uncovered

What did not work as well:

- `auth_session` coverage remained the main weak spot
- some chains were only partially connected because the final source hop was
  not bridged
- candidate-flow repair could preserve a prior usable report, but it did not
  reliably improve coverage or produce a better final writer call
- the discovery path still left gaps around privileged state-changing paths and
  supporting candidate-flow families

The Qwen local provider failure is intentionally ignored for v0.15 planning.
This slice is based on the successful source-navigation behavior and the
remaining quality gaps, not on transport issues.

## Goals

- Recover component recall without losing the stable ledger/report behavior
  already demonstrated by GPT-5.4-mini.
- Improve coverage of `auth_session` so partial chains can be bridged to full
  chains.
- Make candidate-flow repair actually increase useful coverage instead of only
  preserving the last good report.
- Keep report-writer completion and valid-ledger rates high while tightening
  the last hop of incomplete chains.
- Preserve the current static-only posture: no live probing, fuzzing, exploit
  execution, or dynamic scanning.

## Strategy

1. Start with a source-derived focus queue that emphasizes the missing high-risk
   families first, especially `auth_session` and the candidate-flow families
   that still trailed behind.
2. Use controlled entry-point discovery, then follow the chain into supporting
   services, repositories, config, and jobs/consumers.
3. Treat TODO updates as part of the search process so partial evidence is not
   lost when a corrective pass is needed.
4. Keep report writing tied to concrete source evidence rather than forcing a
   no-chain or complete-chain conclusion too early.
5. Use candidate-flow repair only when it can add real source coverage, not just
   regenerate the same report shape.

## Scope And Constraints

- Keep benchmark tooling internal under `codegopher.devtools.benchmark`.
- Keep the chained-audit skill static-only and source-grounded.
- Do not add public benchmark commands.
- Do not treat provider transport failures as model-quality regressions in this
  slice.
- Keep committed documentation sanitized: no raw logs, temp roots, proxy
  snapshots, local endpoints, or original corpus paths.

## Validation

v0.15 should validate the same model path that worked in v0.14 and check for
measurable improvement in the areas that lagged:

- `gpt-5.4-mini` on the sanitized `app-05`, `app-10`, and `app-14` subset.
- `auth_session` coverage and last-hop chain completion.
- Candidate-flow repair effectiveness.
- Report-writer completion and valid-ledger stability.
- Focused recall against the v0.14 baseline, especially component recall.

The success criterion is improvement in the source-discovery and chain-linking
workflow, not transport robustness for the local provider path.

## Success Criteria

- GPT-focused validation regains or improves component recall versus v0.14.
- `auth_session` is no longer the dominant uncovered family in the focused
  subset.
- Candidate-flow repair yields better coverage or clearer failure boundaries.
- Reports remain valid, sanitized, and writer-complete.
- The analysis can still be summarized from source artifacts alone.
