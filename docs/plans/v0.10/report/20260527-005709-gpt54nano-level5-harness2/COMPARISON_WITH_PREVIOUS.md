# Comparison With Previous Structured Run

## Summary

This run expanded the benchmark from the previous two-app very-complex baseline to all nine level-5 apps. Direct comparison is valid only for the overlapping Airline Booking System and Warehouse Management System apps. The aggregate nine-app result is an expanded-scope measurement.

On the overlapping apps, full-chain recall improved from **3/4** to **4/4**, and component recall improved from **11/12** to **12/12**. The cost and request count increased because the run covered nine apps and every app triggered the corrective pass.

## Overlapping-App Delta

| Metric | Previous two-app baseline | New level-5 run | Delta |
|---|---:|---:|---:|
| Full chains | 3/4 | 4/4 | +1 |
| Components | 11/12 | 12/12 | +1 |
| Full-chain recall | 75.0% | 100.0% | +25.0 points |
| Component recall | 91.7% | 100.0% | +8.3 points |
| Missing required evidence | 7 | 5 | -2 |
| Decoy misfires | 0 | 0 | 0 |
| Unmatched candidates | 2 | 2 | 0 |
| Corrective passes | 1/2 | 2/2 | +1 |

## Per-App Delta

| App | Metric | Previous baseline | New run | Delta |
|---|---|---:|---:|---:|
| Airline Booking System | Full chains | 1/2 | 2/2 | +1 |
| Airline Booking System | Components | 5/6 | 6/6 | +1 |
| Airline Booking System | Line refs | 10 | 41 | +31 |
| Airline Booking System | Missing evidence | 5 | 5 | 0 |
| Airline Booking System | Unmatched candidates | 2 | 1 | -1 |
| Warehouse Management System | Full chains | 2/2 | 2/2 | 0 |
| Warehouse Management System | Components | 6/6 | 6/6 | 0 |
| Warehouse Management System | Line refs | 25 | 25 | 0 |
| Warehouse Management System | Missing evidence | 2 | 0 | -2 |
| Warehouse Management System | Unmatched candidates | 0 | 1 | +1 |

## Expanded-Scope Aggregate

| Metric | New level-5 run |
|---|---:|
| Apps | 9 |
| Full chains | 9/11 |
| Components | 30/32 |
| Full-chain recall | 81.8% |
| Component recall | 93.8% |
| JSON ledgers present | 8/9 |
| Exact evidence coverage | 21/98 |
| Safety-clean runs | 9/9 |
| Hygiene-clean workspaces | 9/9 |

## Proxy And Cost Delta

| Metric | Previous two-app baseline | New level-5 run |
|---|---:|---:|
| Apps | 2 | 9 |
| Proxy requests | 32 | 159 |
| Input tokens | 465,630 | 2,164,410 |
| Output tokens | 20,376 | 79,044 |
| Total tokens | 486,006 | 2,243,454 |
| Proxy-reported cost | $0.06689424 | $0.33409596 |
| LLM wall time | 173.423s | 794.191s |
| Provider errors | 0 | 0 |

## Interpretation

The structured focus queue and stricter gates improved overlapping-app recall, especially Airline. The cost increase is expected from the expanded scope and universal corrective pass. The important quality regression is not detection recall; it is that the machine-readable ledger format is still not stable enough. Several reports contained source evidence in prose or nested JSON wrappers that the current parser did not count as exact evidence.

The next gains should come from evidence-ledger robustness and stricter safe-control classification, not simply more model calls.
