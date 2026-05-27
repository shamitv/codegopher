# Harness3 Further Enhancements

## Selection Rule Result

Measured deltas selected four generic follow-up fixes:

| Rule | Result | Selected |
|---|---:|---|
| Validated evidence coverage below 75% | 117/117 = 100.0% | no |
| Focus-category coverage below 75% | 629/967 = 65.0% | yes |
| Full-chain recall below 75% | 7/11 = 63.6% | yes |
| Safe-control unknown rate above 25% | 5/23 = 21.7% | no |
| Unmatched candidates above 1 per app average | 13/9 = 1.44 | yes |
| Token cost per completed chain worsens materially | full proxy cost per completed chain rose from $0.0371 to $0.0553 | yes |

## Follow-Up Fixes To Implement

1. Tighten focus queue ranking and corrective coverage gates.
   - Prioritize high-signal files over repeated same-file matches.
   - Prefer one representative item per path/category before adding lower-value duplicates.
   - During correction, include a compact uncovered-category worklist instead of only generic reminder text.

2. Strengthen bounded review triggers for recall without app-specific hints.
   - Trigger correction when full-chain recall cannot be inferred and high-signal source categories remain uncovered.
   - Ask for a targeted review of uncovered routes, auth checks, helper/generator code, and sinks instead of a broad re-audit.

3. Improve candidate-title and ledger normalization.
   - Normalize title punctuation, arrows, family labels, and status prefixes.
   - Prefer ledger `family` plus source/hop/sink symbols when matching unmatched candidates.

4. Reduce prompt bulk before adding more retrieval.
   - Lower graph edge caps.
   - Render only high-signal graph edges that connect different files or different categories.
   - Keep the focus queue bounded by representative coverage rather than raw match count.

## Expected Impact

These changes should preserve harness3 evidence gains while recovering recall. The goal is not to max out this exact benchmark set; it is to make the harness more generally useful when a model misses quiet helper code, source-controller edges, or safe controls that are present but not path-blocking.

## Verification Plan

- Add focused unit tests for representative focus queue ranking.
- Add tests proving corrective prompts receive compact uncovered-category guidance.
- Add tests for title/ledger normalization.
- Add tests proving source graph caps shrink prompt size and still exclude manifests and removed docs.
- Run focused benchmark tests, Python tests excluding real endpoint smoke, Ruff, and mypy.

## No-Rerun Decision

The full benchmark should not be rerun after these follow-up fixes unless explicitly requested. The reports above are the measured harness3 result; the next code batch should be validated by deterministic tests first.
