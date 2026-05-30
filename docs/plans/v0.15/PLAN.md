# CodeGopher v0.15 Plan - Recall Recovery With Journey Reporting

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

Qwen remains in scope for v0.15. Its v0.14 failure is treated as a transport
blocker, not model-quality evidence. v0.15 must run a lightweight local
Responses/proxy health check before attempting Qwen quality comparison, then
either run the focused benchmark or document the transport block cleanly.

## Goals

- Recover component recall without losing the stable ledger/report behavior
  already demonstrated by GPT-5.4-mini.
- Improve coverage of `auth_session` so partial chains can be bridged to full
  chains.
- Make candidate-flow repair actually increase useful coverage instead of only
  preserving the last good report.
- Keep report-writer completion and valid-ledger rates high while tightening
  the last hop of incomplete chains.
- Keep both `gpt-5.4-mini` and local `Qwen 3.5 35B` in focused validation
  scope, with transport health separated from model quality.
- Produce a sanitized v0.15 journey report that explains what the agent actually
  inspected, repaired, missed, and preserved as last-good.

## Implementation Strategy

- Update the chained-audit skill and/or internal benchmark repair prompts with an
  evidence-first focus queue for uncovered high-risk families: `auth_session`,
  privileged state-changing paths, `repositories_query`, and
  `webhooks_outbound`.
- Require corrective and repair passes to continue from current mission state,
  preserve TODO evidence, and bridge the missing final source hop before
  rewriting chain conclusions.
- Keep report writing tied to concrete source evidence. Do not force a no-chain
  or complete-chain conclusion before the relevant entry point, guard,
  service/repository hop, and sink have been inspected.
- Candidate-flow repair must call `write_chained_vulnerability_report` when the
  writer is available. If a repair pass gathers evidence but misses the writer
  call, classify it as repair failure and preserve the prior last-good report.
- Repair output must show whether it added new `complete`, `incomplete`, or
  `rejected` candidates for the missing families.

## Scope And Constraints

- Keep benchmark tooling internal under `codegopher.devtools.benchmark`.
- Keep the chained-audit skill static-only and source-grounded.
- Do not add public benchmark commands.
- Do not treat provider transport failures as model-quality regressions.
- Do not add cost controls, wall-time budget work, live probing, fuzzing, exploit
  execution, shell execution during audits, MCP calls, arbitrary writes, or
  memory writes.
- Report output must go through the chained-vulnerability report writer when it
  is available; arbitrary `write_file` cleanup is not a successful repair path.
- Keep committed documentation sanitized: no raw logs, temp roots, proxy
  snapshots, endpoint values, API key names or values, local usernames, or
  original corpus paths.

## Validation

Run focused validation on the sanitized `app-05`, `app-10`, and `app-14`
subset:

- `gpt-5.4-mini`.
- Local Responses API alias `Qwen 3.5 35B`.

Before the Qwen benchmark, run a lightweight local Responses/proxy hello check.
If the check fails, document Qwen as transport-blocked and do not count recall
as model quality. If it passes, run the same focused validation as GPT.

Compare:

- Component recall against the v0.14 GPT baseline of `12/19`.
- Complete-chain recall against the v0.14 GPT baseline of `4/8`.
- Valid-ledger rate against the v0.14 GPT baseline of `3/3`.
- Report-writer completion against the v0.14 GPT baseline of `3/3`.
- `auth_session` coverage and last-hop chain completion.
- Candidate-flow repair effectiveness and remaining gaps.
- Provider errors, malformed-tool outcomes, recovered malformed calls, and
  last-good behavior.
- Output leakage, unsafe tool use, and generic security vocabulary diagnostics.

After focused validation, create sanitized v0.15 result docs:

- `docs/plans/v0.15/FOCUSED_VALIDATION.md` with aggregate and per-app results.
- `docs/plans/v0.15/FOCUSED_VALIDATION_JOURNEY.md` with per-model and per-app
  source-navigation behavior, attempts, tool usage, repair behavior, findings,
  misses, and safety/hygiene observations.

If Qwen is transport-blocked, the journey report must explicitly say it did not
reach workspace inspection. If Qwen runs, summarize its actual journey.

## Success Criteria

- GPT component recall improves from `12/19` to at least `13/19`.
- GPT complete-chain recall remains at least `4/8`.
- GPT valid ledgers remain `3/3`.
- GPT report-writer completion remains `3/3`.
- `auth_session` is no longer the dominant uncovered family in the focused
  subset, or the remaining gap is explained with concrete missing-hop evidence.
- Candidate-flow repair either improves coverage or reports a clear bounded
  repair failure without overwriting the last-good report.
- Qwen is either quality-compared after transport health passes or documented as
  transport-blocked with clean diagnostics.
- Reports and committed summaries remain sanitized and source-grounded, with no
  new output leakage or unsafe tool-use regression.
- Full seven-app validation remains blocked until focused validation passes for
  GPT and Qwen is either healthy or explicitly transport-blocked with a clean
  diagnostic.
