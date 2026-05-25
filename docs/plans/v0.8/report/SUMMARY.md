# v0.8 Benchmark Summary

This directory intentionally keeps only the durable benchmark summary. Detailed per-run artifacts such as event logs, stderr logs, generated reports, ground-truth copies, hygiene files, and per-app JSON summaries were removed to keep the repository lightweight.

## Retained Outcomes

| Run | Scope | Requested model | Important caveat | Outcome |
|---|---|---|---|---|
| 20260524-234855-all50 | 50 sanitized sample benchmark apps | Qwen/Qwen3.6-35B-A3B | Historical v0.8 corpus before v0.9 hardening | 47/50 apps fully solved; 110/117 issue components detected; 7 components missed; 4 app-level retries; 0 safety compromises |
| 20260525-180047-gemma-all50 | 50 sanitized sample benchmark apps | google/gemma-4-26B-A4B-it:deepinfra | Proxy later showed Qwen upstream/billing model, so this is not a clean Gemma result | 46/50 apps fully solved; 107/117 issue components detected; 10 components missed; 2 app-level retries; 0 safety compromises |
| 20260525-195911-model-comparison | Comparison of the two all-50 runs | Qwen vs Gemma-requested | Both proxy run snapshots reported Qwen upstream for the Gemma-requested run | Qwen-labeled run had higher strict recall; Gemma-requested run had fewer calls/tokens and lower proxy-reported cost |

## Durable Findings

- The all-50 v0.8 benchmark was static-only and used sanitized code-only temp workspaces.
- No removed evaluator docs, parent paths, original corpus paths, or unsafe tool calls were observed in the aggregate reports.
- The Gemma-requested result should not be used as a model-quality comparison because the proxy route served Qwen upstream.
- Most v0.8 misses were not subtle reasoning misses; several were operational misses where no report was generated or malformed tool-call JSON ended the run.
- These failures motivated v0.9 harder manifests and v0.10 mission-contract completion gates.

## Example Compact Future Entry

| Run | Scope | Model | Apps full | Chains | Components | Retries | Safety | Notes |
|---|---|---|---:|---:|---:|---:|---|---|
| 20260601-120000-qwen-sample | 5 sanitized apps | Qwen/Qwen3.6-35B-A3B | 4/5 | 8/10 | 23/27 | 1 | clean | Store raw artifacts outside git; keep only this summary in repo |

