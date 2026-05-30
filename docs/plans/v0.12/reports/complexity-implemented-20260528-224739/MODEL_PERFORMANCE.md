# Implemented Complexity-App Model Performance

- Stamp: `20260528-224739`
- Scope: seven implemented apps from the complexity upgrade index.
- Raw artifacts remain outside committed docs; this report uses aggregate sanitized metrics only.

## Model Summary

| Model | Components | Chains | Valid ledgers | Evidence | Discovery | Corrections | Retries | Requests | Tokens | Cost | Wall time |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| deepseek-v4-flash | 33/41 (80.5%) | 11/17 (64.7%) | 3/7 | 189/189 (100.0%) | 7/7 | 7/7 | 1/7 | 271 | 10333681 | $1.3565 | 1h |
| Qwen/Qwen3.6-35B-A3B:deepinfra | 26/41 (63.4%) | 9/17 (52.9%) | 2/7 | 93/98 (94.9%) | 7/7 | 5/7 | 4/7 | 349 | 12425737 | $2.3209 | 1h 29m |
| gpt-5.4-mini | 22/41 (53.7%) | 5/17 (29.4%) | 6/7 | 149/149 (100.0%) | 5/7 | 3/7 | 0/7 | 61 | 1385608 | $1.2463 | 6m 37s |
| google/gemma-4-31B-it:deepinfra | 22/41 (53.7%) | 4/17 (23.5%) | 5/7 | 91/92 (98.9%) | 3/7 | 6/7 | 0/7 | 171 | 2548127 | $0.3460 | 1h 16m |
| google/gemma-4-26B-A4B-it:deepinfra | 16/41 (39.0%) | 4/17 (23.5%) | 4/7 | 59/59 (100.0%) | 3/7 | 7/7 | 0/7 | 232 | 2948660 | $0.2213 | 31m 28s |
| gpt-5.4-nano | 11/41 (26.8%) | 2/17 (11.8%) | 6/7 | 99/99 (100.0%) | 4/7 | 6/7 | 0/7 | 121 | 3110608 | $0.6880 | 11m 1s |

## Ranking Signals

- Best component recall: deepseek-v4-flash at 80.5%.
- Best complete-chain recall: deepseek-v4-flash at 64.7%.
- Best ledger validity count: gpt-5.4-mini with 6/7 valid ledgers.
- Lowest observed cost: google/gemma-4-26B-A4B-it:deepinfra at $0.2213.
- Shortest observed wall time: gpt-5.4-mini at 6m 37s.

## By App

### app-01: E-Commerce Product Catalog API

| Model | Components | Chains | Ledger | Evidence | Discovery | Attempts | Correction | Retry |
|---|---:|---:|---|---:|---|---:|---|---|
| gpt-5.4-nano | 2/7 (28.6%) | 0/3 (0.0%) | yes | 13/13 | partial | 2 | yes | no |
| gpt-5.4-mini | 2/7 (28.6%) | 0/3 (0.0%) | yes | 18/18 | complete | 2 | yes | no |
| deepseek-v4-flash | 2/7 (28.6%) | 0/3 (0.0%) | no | 32/32 | complete | 3 | yes | yes |
| google/gemma-4-31B-it:deepinfra | 1/7 (14.3%) | 0/3 (0.0%) | yes | 14/14 | complete | 2 | yes | no |
| google/gemma-4-26B-A4B-it:deepinfra | 0/7 (0.0%) | 0/3 (0.0%) | no | 4/4 | complete | 2 | yes | no |
| Qwen/Qwen3.6-35B-A3B:deepinfra | 0/7 (0.0%) | 0/3 (0.0%) | no | 0/0 | complete | 2 | no | yes |

### app-05: Online Learning Management System

| Model | Components | Chains | Ledger | Evidence | Discovery | Attempts | Correction | Retry |
|---|---:|---:|---|---:|---|---:|---|---|
| gpt-5.4-mini | 5/7 (71.4%) | 1/3 (33.3%) | yes | 28/28 | partial | 1 | no | no |
| deepseek-v4-flash | 5/7 (71.4%) | 1/3 (33.3%) | yes | 24/24 | complete | 2 | yes | no |
| google/gemma-4-31B-it:deepinfra | 4/7 (57.1%) | 1/3 (33.3%) | yes | 16/16 | partial | 2 | yes | no |
| Qwen/Qwen3.6-35B-A3B:deepinfra | 4/7 (57.1%) | 1/3 (33.3%) | yes | 26/26 | complete | 2 | yes | no |
| google/gemma-4-26B-A4B-it:deepinfra | 3/7 (42.9%) | 1/3 (33.3%) | yes | 9/9 | partial | 2 | yes | no |
| gpt-5.4-nano | 1/7 (14.3%) | 0/3 (0.0%) | yes | 25/25 | complete | 2 | yes | no |

### app-06: Enterprise HR Management System

| Model | Components | Chains | Ledger | Evidence | Discovery | Attempts | Correction | Retry |
|---|---:|---:|---|---:|---|---:|---|---|
| deepseek-v4-flash | 6/6 (100.0%) | 3/3 (100.0%) | no | 29/29 | complete | 2 | yes | no |
| Qwen/Qwen3.6-35B-A3B:deepinfra | 5/6 (83.3%) | 2/3 (66.7%) | yes | 37/37 | complete | 2 | yes | no |
| google/gemma-4-31B-it:deepinfra | 4/6 (66.7%) | 1/3 (33.3%) | no | 12/13 | complete | 2 | yes | no |
| gpt-5.4-nano | 2/6 (33.3%) | 0/3 (0.0%) | yes | 11/11 | partial | 1 | no | no |
| google/gemma-4-26B-A4B-it:deepinfra | 1/6 (16.7%) | 0/3 (0.0%) | yes | 13/13 | complete | 2 | yes | no |
| gpt-5.4-mini | 0/6 (0.0%) | 0/3 (0.0%) | yes | 16/16 | complete | 2 | yes | no |

### app-07: Airline Booking System

| Model | Components | Chains | Ledger | Evidence | Discovery | Attempts | Correction | Retry |
|---|---:|---:|---|---:|---|---:|---|---|
| deepseek-v4-flash | 5/6 (83.3%) | 1/2 (50.0%) | no | 22/22 | complete | 2 | yes | no |
| Qwen/Qwen3.6-35B-A3B:deepinfra | 5/6 (83.3%) | 1/2 (50.0%) | no | 0/0 | complete | 3 | yes | yes |
| gpt-5.4-mini | 4/6 (66.7%) | 0/2 (0.0%) | yes | 16/16 | complete | 1 | no | no |
| google/gemma-4-31B-it:deepinfra | 4/6 (66.7%) | 0/2 (0.0%) | yes | 14/14 | partial | 2 | yes | no |
| google/gemma-4-26B-A4B-it:deepinfra | 3/6 (50.0%) | 1/2 (50.0%) | yes | 7/7 | partial | 2 | yes | no |
| gpt-5.4-nano | 0/6 (0.0%) | 0/2 (0.0%) | yes | 12/12 | complete | 2 | yes | no |

### app-10: Telecom Billing Platform

| Model | Components | Chains | Ledger | Evidence | Discovery | Attempts | Correction | Retry |
|---|---:|---:|---|---:|---|---:|---|---|
| deepseek-v4-flash | 6/6 (100.0%) | 2/2 (100.0%) | yes | 24/24 | complete | 2 | yes | no |
| Qwen/Qwen3.6-35B-A3B:deepinfra | 6/6 (100.0%) | 2/2 (100.0%) | no | 30/35 | complete | 2 | yes | no |
| google/gemma-4-31B-it:deepinfra | 5/6 (83.3%) | 1/2 (50.0%) | yes | 13/13 | complete | 2 | yes | no |
| google/gemma-4-26B-A4B-it:deepinfra | 5/6 (83.3%) | 1/2 (50.0%) | no | 5/5 | complete | 2 | yes | no |
| gpt-5.4-nano | 3/6 (50.0%) | 1/2 (50.0%) | yes | 17/17 | complete | 2 | yes | no |
| gpt-5.4-mini | 3/6 (50.0%) | 1/2 (50.0%) | yes | 16/16 | complete | 1 | no | no |

### app-11: Social Media Analytics Dashboard

| Model | Components | Chains | Ledger | Evidence | Discovery | Attempts | Correction | Retry |
|---|---:|---:|---|---:|---|---:|---|---|
| gpt-5.4-mini | 3/3 (100.0%) | 1/1 (100.0%) | yes | 20/20 | complete | 1 | no | no |
| deepseek-v4-flash | 3/3 (100.0%) | 1/1 (100.0%) | yes | 26/26 | complete | 2 | yes | no |
| google/gemma-4-31B-it:deepinfra | 1/3 (33.3%) | 0/1 (0.0%) | no | 9/9 | partial | 2 | yes | no |
| google/gemma-4-26B-A4B-it:deepinfra | 1/3 (33.3%) | 0/1 (0.0%) | no | 8/8 | partial | 2 | yes | no |
| gpt-5.4-nano | 0/3 (0.0%) | 0/1 (0.0%) | yes | 8/8 | partial | 2 | yes | no |
| Qwen/Qwen3.6-35B-A3B:deepinfra | 0/3 (0.0%) | 0/1 (0.0%) | no | 0/0 | complete | 2 | no | yes |

### app-14: Telemedicine Appointment System

| Model | Components | Chains | Ledger | Evidence | Discovery | Attempts | Correction | Retry |
|---|---:|---:|---|---:|---|---:|---|---|
| deepseek-v4-flash | 6/6 (100.0%) | 3/3 (100.0%) | no | 32/32 | complete | 2 | yes | no |
| Qwen/Qwen3.6-35B-A3B:deepinfra | 6/6 (100.0%) | 3/3 (100.0%) | no | 0/0 | complete | 3 | yes | yes |
| gpt-5.4-mini | 5/6 (83.3%) | 2/3 (66.7%) | no | 35/35 | partial | 2 | yes | no |
| gpt-5.4-nano | 3/6 (50.0%) | 1/3 (33.3%) | no | 13/13 | complete | 2 | yes | no |
| google/gemma-4-31B-it:deepinfra | 3/6 (50.0%) | 1/3 (33.3%) | yes | 13/13 | partial | 1 | no | no |
| google/gemma-4-26B-A4B-it:deepinfra | 3/6 (50.0%) | 1/3 (33.3%) | yes | 13/13 | partial | 2 | yes | no |

## By Language

| Language | Model | Components | Chains | Discovery complete |
|---|---|---:|---:|---:|
| Python | Qwen/Qwen3.6-35B-A3B:deepinfra | 4/14 (28.6%) | 1/6 (16.7%) | 2/2 |
| Python | deepseek-v4-flash | 7/14 (50.0%) | 1/6 (16.7%) | 2/2 |
| Python | gpt-5.4-nano | 3/14 (21.4%) | 0/6 (0.0%) | 1/2 |
| Python | gpt-5.4-mini | 7/14 (50.0%) | 1/6 (16.7%) | 1/2 |
| Python | google/gemma-4-26B-A4B-it:deepinfra | 3/14 (21.4%) | 1/6 (16.7%) | 1/2 |
| Python | google/gemma-4-31B-it:deepinfra | 5/14 (35.7%) | 1/6 (16.7%) | 1/2 |
| Java | Qwen/Qwen3.6-35B-A3B:deepinfra | 16/18 (88.9%) | 5/7 (71.4%) | 3/3 |
| Java | deepseek-v4-flash | 17/18 (94.4%) | 6/7 (85.7%) | 3/3 |
| Java | gpt-5.4-nano | 5/18 (27.8%) | 1/7 (14.3%) | 2/3 |
| Java | gpt-5.4-mini | 7/18 (38.9%) | 1/7 (14.3%) | 3/3 |
| Java | google/gemma-4-26B-A4B-it:deepinfra | 9/18 (50.0%) | 2/7 (28.6%) | 2/3 |
| Java | google/gemma-4-31B-it:deepinfra | 13/18 (72.2%) | 2/7 (28.6%) | 2/3 |
| TypeScript | Qwen/Qwen3.6-35B-A3B:deepinfra | 6/9 (66.7%) | 3/4 (75.0%) | 2/2 |
| TypeScript | deepseek-v4-flash | 9/9 (100.0%) | 4/4 (100.0%) | 2/2 |
| TypeScript | gpt-5.4-nano | 3/9 (33.3%) | 1/4 (25.0%) | 1/2 |
| TypeScript | gpt-5.4-mini | 8/9 (88.9%) | 3/4 (75.0%) | 1/2 |
| TypeScript | google/gemma-4-26B-A4B-it:deepinfra | 4/9 (44.4%) | 1/4 (25.0%) | 0/2 |
| TypeScript | google/gemma-4-31B-it:deepinfra | 4/9 (44.4%) | 1/4 (25.0%) | 0/2 |

## Takeaways

- DeepSeek had the strongest recall, but several high-recall reports failed ledger validity checks.
- GPT 5.4 Mini produced the best ledger-validity profile and the fastest run, but recall was middle of the pack and cost was high relative to its token volume.
- Qwen was second on recall but had the highest request, token, cost, wall-time, and retry burden.
- Gemma 26B was the least expensive but missed many components. Gemma 31B improved recall over 26B, but was much slower per request.
- GPT 5.4 Nano was quick and usually produced valid ledgers, but recall was the weakest overall.
