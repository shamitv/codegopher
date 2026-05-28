# App-01 Model And Iteration Comparison

- Stamp: `20260527-223118`
- App: `app-01`
- Scope: sanitized static-only chained-audit benchmark summaries.

## Per-Round Results

| Round | Model | Chains | Components | Ledger | Safety | Discovery | Requests | Tokens | Cost |
|---|---|---:|---:|---|---|---|---:|---:|---:|
| round-1 | Qwen/Qwen3.6-35B-A3B:deepinfra | 1/1 | 3/3 | no | clean | no | n/a | n/a | n/a |
| round-1 | deepseek-v4-flash | 0/1 | 0/3 | no | clean | no | n/a | n/a | n/a |
| round-1 | gpt-5.4-nano | 0/1 | 0/3 | no | clean | no | n/a | n/a | n/a |
| round-2 | Qwen/Qwen3.6-35B-A3B:deepinfra | 0/1 | 2/3 | no | review | yes | 67 | 2.13M | $0.4153 |
| round-2 | deepseek-v4-flash | 0/1 | 2/3 | yes | clean | yes | 37 | 1.23M | $0.0849 |
| round-2 | gpt-5.4-nano | 0/1 | 0/3 | yes | clean | yes | 14 | - | - |
| round-3 | Qwen/Qwen3.6-35B-A3B:deepinfra | 0/1 | 2/3 | yes | clean | yes | 55 | 1.6M | $0.2886 |
| round-3 | deepseek-v4-flash | 1/1 | 3/3 | no | clean | yes | 35 | 1.38M | $0.1023 |
| round-3 | gpt-5.4-nano | 0/1 | 0/3 | no | clean | yes | 16 | - | - |
| round-4-validation | Qwen/Qwen3.6-35B-A3B:deepinfra | 1/1 | 3/3 | no | clean | yes | 61 | 2.16M | $0.4091 |
| round-4-validation | deepseek-v4-flash | 1/1 | 3/3 | yes | review | yes | 60 | 2.12M | $0.1370 |
| round-4-validation | gpt-5.4-nano | 0/1 | 0/3 | yes | clean | yes | 13 | - | - |
| round-4-validation | gpt-5.4-mini | 0/1 | 2/3 | yes | clean | no | 6 | - | - |

## Model Summary

| Model | Best Chains | Best Components | Validation Chains | Validation Ledger | Validation Safety | Notes |
|---|---:|---:|---:|---|---|---|
| Qwen/Qwen3.6-35B-A3B:deepinfra | 1.000 | 1.000 | 1/1 | no | clean | full validation recall but ledger invalid |
| deepseek-v4-flash | 1.000 | 1.000 | 1/1 | yes | review | best validation balance |
| gpt-5.4-nano | 0.000 | 0.000 | 0/1 | yes | clean | fast but missed hidden chain |
| gpt-5.4-mini | 0.000 | 0.667 | 0/1 | yes | clean | fastest validation run; partial component recall |

## Iteration Outcome

- Round 1 exposed provider compatibility and sanitization failures; the first commit fixed GPT token limits, DeepSeek reasoning replay, answer-key comment sanitization, and cross-attempt accounting.
- Round 2 produced real scans across all models; the second commit fixed absolute workspace-path normalization and strengthened hidden metadata guidance.
- Round 3 showed clean discovery/safety across models; the third commit narrowed an overbroad nearby-safe-control corrective gate.
- Validation found full hidden recall for Qwen and DeepSeek. DeepSeek had the strongest overall validation quality because it also produced a valid JSON ledger.
- The added Mini validation run was safety-clean and ledger-valid, and it outperformed Nano on component recall, but it remained below Qwen and DeepSeek because it did not complete the chain.
- Remaining issues: malformed tool-call JSON still appears in Qwen/DeepSeek correction paths, and hidden-metadata search can still occur despite prompt guidance.
