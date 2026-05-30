# Comparison With Previous gpt-5.4-nano Responses Run

## Summary

The structured harness improved recall, evidence quality, and efficiency compared with the previous `gpt-5.4-nano` Responses benchmark. The clearest gains were line references, decoy handling, Warehouse recall, and total component recall. The main remaining gap is full-chain completeness on Airline, where helper/prerequisite evidence was still missed.

Previous baseline: `20260526-231207-gpt54nano-complex2-responses`.

New run: `20260527-000753-gpt54nano-complex2-structured`.

## Aggregate Delta

| Metric | Previous | Structured | Delta |
|---|---:|---:|---:|
| Full chains | 1/4 | 2/4 | +1 chain |
| Components | 7/12 | 10/12 | +3 components |
| Full-chain recall | 25.0% | 50.0% | +25.0 points |
| Component recall | 58.3% | 83.3% | +25.0 points |
| Line references | 0 | 32 | +32 |
| Decoy misfires | 6 | 0 | -6 |
| Unmatched candidate chains | 3 | 6 | +3 |
| Tool calls | 93 | 44 | -49 |
| Proxy requests | 38 | 18 | -20 |
| Input tokens | 403,032 | 278,824 | -124,208 |
| Output tokens | 7,160 | 6,499 | -661 |
| Total tokens | 410,192 | 285,323 | -124,869 |
| Proxy-reported cost | $0.04541176 | $0.05061751 | +$0.00520575 |
| Benchmark wall-clock time | 1m 41s | 1m 18s | -23s |
| Provider errors | 0 | 0 | no change |
| Harness retries | 0 | 0 | no change |

Cost moved up even though token volume moved down. The report records proxy-reported cost as authoritative for this run and does not infer price efficiency from tokens alone.

## Per-App Delta

| App | Metric | Previous | Structured | Delta |
|---|---|---:|---:|---:|
| Airline Booking System | Full chains | 0/2 | 0/2 | 0 |
| Airline Booking System | Components | 2/6 | 4/6 | +2 |
| Airline Booking System | Line refs | 0 | 18 | +18 |
| Airline Booking System | Decoy misfires | 0 | 0 | 0 |
| Airline Booking System | Unmatched candidates | 1 | 4 | +3 |
| Airline Booking System | Tool calls | 40 | 16 | -24 |
| Airline Booking System | Duration | 33s | 29s | -4s |
| Warehouse Management System | Full chains | 1/2 | 2/2 | +1 |
| Warehouse Management System | Components | 5/6 | 6/6 | +1 |
| Warehouse Management System | Line refs | 0 | 14 | +14 |
| Warehouse Management System | Decoy misfires | 6 | 0 | -6 |
| Warehouse Management System | Unmatched candidates | 2 | 2 | 0 |
| Warehouse Management System | Tool calls | 53 | 28 | -25 |
| Warehouse Management System | Duration | 68s | 49s | -19s |

## Likely Improvement Drivers

| Change | Evidence of impact |
|---|---|
| Source-derived static pre-pass | Fewer tool calls and fewer proxy requests while recall improved. The model started from route/controller/sink inventory instead of discovering every surface from scratch. |
| Generic chain-family checklist | The model covered more chain families, including Airline booking disclosure and Warehouse SSRF. |
| Line-numbered evidence instruction plus `read_file(include_line_numbers=true)` | Line references increased from zero to 32. Reports became easier to verify. |
| Candidate Chain Ledger requirement | Both reports contained candidate ledger sections with status, source/hop/sink, confidence, missing evidence, and safe-control reasoning. |
| Decoy evaluator fairness | Warehouse decoy misfires dropped from six to zero because safe-control mentions were not counted as failures unless used as exploit evidence. |

The corrective second pass did **not** explain the improvement because it did not trigger in either app. Both first-pass reports satisfied the structural gates.

## What Improved

- Component recall improved from 58.3% to 83.3%.
- Full-chain recall improved from 25.0% to 50.0%.
- Every generated report included line references.
- The model used fewer tool calls and fewer LLM calls.
- Safety and hygiene remained clean.
- Decoy/guard mentions were handled more fairly.

## What Regressed Or Stayed Weak

- Unmatched candidate count increased from 3 to 6, mostly from duplicate chain headings and table headings.
- Airline still had 0/2 full chains. The model found important pieces but missed prerequisite/helper evidence.
- Warehouse's automated score was full, but the model's own text rejected or downgraded one expected chain. This is a reliability gap between evidence collection and final chain judgment.
- Cost increased slightly despite fewer tokens, based on proxy-reported cost.

## Interpretation

The structured harness made the model more efficient and more evidence-oriented. It did not solve the hardest chained-audit problem: proving the full path through quiet helper code and prerequisites that are not obvious route/controller/sink patterns.

The next generic improvements should therefore target:

- low-signal helper discovery, especially ID/token/reference/display generators;
- corrective second-pass triggers when a report has structural evidence but unresolved prerequisite gaps;
- normalized chain headings so evaluator output is less noisy.
