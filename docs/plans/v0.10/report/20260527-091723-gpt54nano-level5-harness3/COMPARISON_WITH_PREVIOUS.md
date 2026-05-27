# Harness3 vs Harness2 Comparison

## Summary

Harness3 improved machine-readable evidence quality but reduced vulnerability recall. The delta suggests the harness became stricter without becoming better at steering the model toward incomplete source coverage.

The comparison baseline is `20260527-005709-gpt54nano-level5-harness2`.

## Aggregate Delta

| Metric | Harness2 | Harness3 | Delta |
|---|---:|---:|---:|
| Full-chain recall | 9/11 = 81.8% | 7/11 = 63.6% | -18.2 pts |
| Component recall | 30/32 = 93.8% | 27/32 = 84.4% | -9.4 pts |
| Exact evidence coverage | 21/98 = 21.4% | 117/117 = 100.0% | +78.6 pts |
| Valid ledgers | not measured | 7/9 | new metric |
| JSON/validated ledgers present | 8/9 JSON ledgers | 7/9 valid ledgers | stricter metric |
| Focus-category coverage | not measured | 629/967 = 65.0% | new metric |
| Corrective passes | 9/9 | 8/9 | -1 |
| Tool calls | 232 | 254 | +22 |
| Unmatched candidates | 8 | 13 | +5 |
| Decoy misfires | 0 | 0 | no change |
| Full proxy requests | 159 | 161 | +2 |
| Full proxy total tokens | 2,243,454 | 2,703,113 | +459,659 |
| Full proxy cost | $0.33409596 | $0.38679010 | +$0.05269414 |
| Full proxy open duration | 13m 16s | 12m 12s | -1m 04s |

Primary benchmark-only stats for harness3 were 153 Responses requests, 2,535,758 tokens, and $0.36991300. The full proxy bucket includes a mixed-model caveat, so cost deltas should be read as approximate.

## Per-App Recall Delta

| App | Harness2 chains | Harness3 chains | Harness2 components | Harness3 components | Direction |
|---|---:|---:|---:|---:|---|
| E-Commerce Product Catalog API | 0/1 | 0/1 | 2/3 | 2/3 | unchanged |
| Online Learning Management System | 0/1 | 1/1 | 2/3 | 3/3 | improved |
| Enterprise HR Management System | 1/1 | 1/1 | 2/2 | 2/2 | unchanged |
| Airline Booking System | 2/2 | 1/2 | 6/6 | 5/6 | regressed |
| Warehouse Management System | 2/2 | 1/2 | 6/6 | 5/6 | regressed |
| Telecom Billing Platform | 1/1 | 0/1 | 3/3 | 1/3 | regressed |
| Social Media Analytics Dashboard | 1/1 | 1/1 | 3/3 | 3/3 | unchanged |
| IoT Device Dashboard | 1/1 | 1/1 | 3/3 | 3/3 | unchanged |
| Parking Management System | 1/1 | 1/1 | 3/3 | 3/3 | unchanged |

## Interpretation

Likely improvements from harness3:

- Validated-ledger parsing and stricter evidence wording materially improved exact machine-readable evidence.
- Focus coverage exposed specific omitted review categories, which harness2 could not quantify.
- Source graph context gave more line-numbered navigation hints without leaking evaluator data.

Likely regressions from harness3:

- Prompt and context bulk increased. The model may have spent more budget satisfying schema and graph instructions rather than exploring chain alternatives.
- The corrective pass was too evidence-oriented. It repaired structure but did not reliably reopen missed high-signal categories.
- Focus coverage gates were measured after the fact but did not sufficiently reshape the corrective pass toward uncovered categories.
- Title normalization did not keep up with the richer ledger output, increasing unmatched candidates.

## Cost And Efficiency

| Metric | Harness2 | Harness3 primary | Harness3 full proxy |
|---|---:|---:|---:|
| Cost per completed full chain | $0.0371 | $0.0528 | $0.0553 |
| Tokens per completed full chain | 249,273 | 362,251 | 386,159 |
| Tool calls per completed full chain | 25.8 | 36.3 | 36.3 |

Harness3 was more expensive per completed chain because recall decreased while token volume increased. The next change should reduce prompt bulk and use focus gaps more selectively.

## Conclusion

Harness3 is a clear evidence-quality improvement and a recall regression. The next fix should not add more generic text. It should tighten retrieval: rank focus items better, give the corrective pass a short uncovered-category worklist, and normalize candidate titles without inflating the prompt.
