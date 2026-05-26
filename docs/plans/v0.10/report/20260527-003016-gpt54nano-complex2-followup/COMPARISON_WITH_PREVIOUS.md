# Comparison With Previous Structured Run

## Summary

The post-follow-up run improved chain and component recall compared with `20260527-000753-gpt54nano-complex2-structured`. The most meaningful gain was Airline: it moved from 0/2 full chains to 1/2 and from 4/6 components to 5/6. Warehouse stayed full by automated scoring, but the corrective pass made the report more explicit and eliminated unmatched candidate headings.

## Aggregate Delta

| Metric | Previous structured | Post-follow-up | Delta |
|---|---:|---:|---:|
| Full chains | 2/4 | 3/4 | +1 chain |
| Components | 10/12 | 11/12 | +1 component |
| Full-chain recall | 50.0% | 75.0% | +25.0 points |
| Component recall | 83.3% | 91.7% | +8.4 points |
| Line references | 32 | 35 | +3 |
| Missing required evidence | 5 | 7 | +2 |
| Decoy misfires | 0 | 0 | 0 |
| Unmatched candidate chains | 6 | 2 | -4 |
| Tool calls | 44 | 61 | +17 |
| Proxy requests | 18 | 32 | +14 |
| Input tokens | 278,824 | 465,630 | +186,806 |
| Output tokens | 6,499 | 20,376 | +13,877 |
| Total tokens | 285,323 | 486,006 | +200,683 |
| Proxy-reported cost | $0.05061751 | $0.06689424 | +$0.01627673 |
| Provider errors | 0 | 0 | no change |

## Per-App Delta

| App | Metric | Previous structured | Post-follow-up | Delta |
|---|---|---:|---:|---:|
| Airline Booking System | Full chains | 0/2 | 1/2 | +1 |
| Airline Booking System | Components | 4/6 | 5/6 | +1 |
| Airline Booking System | Line refs | 18 | 10 | -8 |
| Airline Booking System | Missing evidence | 5 | 5 | 0 |
| Airline Booking System | Unmatched candidates | 4 | 2 | -2 |
| Airline Booking System | Tool calls | 16 | 34 | +18 |
| Warehouse Management System | Full chains | 2/2 | 2/2 | 0 |
| Warehouse Management System | Components | 6/6 | 6/6 | 0 |
| Warehouse Management System | Line refs | 14 | 25 | +11 |
| Warehouse Management System | Missing evidence | 0 | 2 | +2 |
| Warehouse Management System | Unmatched candidates | 2 | 0 | -2 |
| Warehouse Management System | Corrective pass | no | yes | +1 |
| Warehouse Management System | Tool calls | 28 | 27 | -1 |

## Likely Improvement Drivers

| Change | Evidence of impact |
|---|---|
| Events-stdin prompt transport | Fixed the pre-proxy Windows argument expansion failure caused by long structured prompts. |
| Quiet-helper and prerequisite prompt expansion | Airline recall improved, especially the injection chain, though PNR generation still remained missed. |
| Corrective second-pass trigger | Triggered for Warehouse and produced a cleaner final report with no unmatched candidate headings. |
| Candidate-title normalization | Unmatched candidate chains dropped from 6 to 2. |
| Decoy scoring and skill language | Decoy misfires stayed at zero. |

## What Improved

- Full-chain recall reached 75.0%.
- Component recall reached 91.7%.
- Airline improved from no full chains to one full chain.
- Warehouse retained full automated recall.
- Unmatched candidate count dropped by two-thirds.
- The harness surfaced and fixed a real Windows prompt-transport failure.

## What Regressed Or Stayed Weak

- Cost and token usage increased because the current run involved more reading and one corrective pass.
- Missing required evidence increased from 5 to 7 because reports still used abbreviated filenames/symbols in places.
- Airline still missed the PNR generator prerequisite.
- Warehouse still contained a tension between “complete” scoring and incomplete/partially inferred wording for some path links.

## Interpretation

The harness changes improved detection quality, but the next gains should come from exact evidence enforcement rather than broader search alone. The benchmark now shows enough chain discovery; the weak spot is that the model does not always put the exact full relative path and exact method/symbol into the final ledger row that the evaluator and an analyst can verify.
