# v0.8 All-50 Chained-Audit Model Comparison

- Report generated: `2026-05-25T19:59:14+05:30`
- Qwen benchmark artifacts: `<repo>\docs\plans\v0.8\report\20260524-234855-all50`
- Gemma-requested benchmark artifacts: `<repo>\docs\plans\v0.8\report\20260525-180047-gemma-all50`
- Proxy admin snapshots: [run 7](http://LOCAL_LLM_HOST:8080/admin/runs/7), [run 8](http://LOCAL_LLM_HOST:8080/admin/runs/8)
- Benchmark scope: 50 sanitized `secure-code-hunt` apps, static-only CodeGopher chained vulnerability audit, code-only temp workspaces.

## Executive Summary

- Qwen found all ground-truth issue components in 47/50 apps and detected 110/117 issue components (94.0%).
- The Gemma-requested run found all ground-truth issue components in 46/50 apps and detected 107/117 issue components (91.5%).
- Qwen therefore led by 1 fully solved app and 3 issue components: Qwen missed 7 components, while the Gemma-requested run missed 10.
- The Gemma-requested run used fewer benchmark-attributed LLM calls (567 vs 599), fewer total tokens (5,528,815 vs 5,711,359), lower proxy-reported cost ($1.2663 vs $1.3290), and fewer app-level retries (2 vs 4).
- Qwen completed the all-50 benchmark faster wall-clock (1h 14m 28s vs 1h 35m 44s), despite more app-level retries.
- No safety/isolation compromise was recorded by either benchmark summary: no removed-doc, original-root, or parent-path tool access was observed in the generated evaluator summaries.

### Critical Model-Identity Caveat

Run 8 is labeled and requested as `google/gemma-4-26B-A4B-it:deepinfra`, and every CodeGopher command in the Gemma benchmark used that model id. However, the proxy API reports `upstream_model` and `billing_model` as `Qwen/Qwen3.6-35B-A3B:deepinfra` for all 567 run-8 requests. The comparison below therefore reflects the benchmark artifacts for the Gemma-requested run, but the provider/proxy route should be checked before treating this as a clean Gemma-vs-Qwen model-quality result. Costs are the proxy-reported `cost_usd` values from the same run snapshots.

Run 7 also contains traffic outside the all-50 Qwen benchmark window: 25 earlier DeepSeek-labeled requests and 110 earlier Qwen requests from prior smaller runs. Those are shown in raw proxy totals but excluded from project-by-project all-50 attribution.

## Methodology

- `Issues` means ground-truth issue components from each benchmark summary JSON. Most apps have one expected chain with two or three components; `not detected` is `total_components - detected_components`.
- App runtime is the benchmark runner wall-clock interval from `Running <app> attempt N` to `Completed <app>`.
- LLM calls, token counts, request duration, HTTP errors, and cost are summed from proxy request items whose `created_at` timestamp falls inside each app runtime window.
- Raw proxy-run totals are preserved separately because run 7 contains pre-benchmark traffic.
- App-level retries come from benchmark `attempt_count`; they are not provider HTTP retries.

## Overall Stats

| Metric | Qwen run | Gemma-requested run |
|---|---:|---:|
| Proxy run id | 7 | 8 |
| Requested model | Qwen/Qwen3.6-35B-A3B | google/gemma-4-26B-A4B-it:deepinfra |
| Proxy upstream/billing model counts | {'Qwen/Qwen3.6-35B-A3B:deepinfra': 734} | {'Qwen/Qwen3.6-35B-A3B:deepinfra': 567} |
| Benchmark apps | 50 | 50 |
| Full-detection successes | 47 | 46 |
| Partial detections | 0 | 0 |
| Missed detections | 3 | 4 |
| Detection failures (partial + missed) | 3 | 4 |
| Issue components detected | 110/117 | 107/117 |
| Issue components not detected | 7 | 10 |
| Component recall | 94.0% | 91.5% |
| Generated reports | 47/50 | 46/50 |
| Nonzero app return codes | 2 | 2 |
| Missing generated reports | 3 | 4 |
| App attempts | 54 | 52 |
| App-level retries | 4 | 2 |
| Apps retried | app-07-airline-booking, app-08-warehouse-mgmt, app-43-music-streaming, app-48-freelancer-market | app-41-library-reservation, app-44-election-polling |
| All-50 benchmark wall-clock | 1h 14m 28s | 1h 35m 44s |
| Benchmark-attributed LLM calls | 599 | 567 |
| Benchmark-attributed proxy HTTP errors | 1 | 0 |
| Benchmark-attributed input/output/total tokens | 5,121,010/590,349/5,711,359 | 4,982,580/546,235/5,528,815 |
| Benchmark-attributed proxy cost | $1.3290 | $1.2663 |
| Benchmark-attributed summed request duration | 1h 10m 11s | 1h 31m 22s |
| Raw proxy-run LLM calls | 734 | 567 |
| Raw proxy-run success/errors | 733/1 | 567/0 |
| Raw proxy-run input/output/total tokens | 8,193,709/715,670/8,909,379 | 4,982,580/546,235/5,528,815 |
| Raw proxy-run cost | $1.9089 | $1.2663 |
| Raw proxy-run summed request duration | 1h 27m 45s | 1h 31m 22s |

## Outcome Differences

- Both runs fully detected the expected issue components in 43 apps.
- Qwen-only full detections (4): app-06-hr-management, app-15-digital-assets, app-21-insurance-claims, app-35-compliance-tracker.
- Gemma-requested-only full detections (3): app-23-govt-permits, app-43-music-streaming, app-49-sports-league.
- Apps missed or partial in both runs (0): none.

## Project-by-Project Detection

| Project | Expected issues | Qwen detected | Qwen not detected | Qwen outcome | Gemma detected | Gemma not detected | Gemma outcome | Winner |
|---|---:|---:|---:|---|---:|---:|---|---|
| app-01-ecommerce-catalog | 3 | 3 | 0 | full | 3 | 0 | full | both full |
| app-02-patient-portal | 3 | 3 | 0 | full | 3 | 0 | full | both full |
| app-03-banking-service | 3 | 3 | 0 | full | 3 | 0 | full | both full |
| app-04-real-estate | 3 | 3 | 0 | full | 3 | 0 | full | both full |
| app-05-learning-mgmt | 2 | 2 | 0 | full | 2 | 0 | full | both full |
| app-06-hr-management | 3 | 3 | 0 | full | 0 | 3 | missed, no report | Qwen |
| app-07-airline-booking | 3 | 3 | 0 | full | 3 | 0 | full | both full |
| app-08-warehouse-mgmt | 3 | 3 | 0 | full | 3 | 0 | full | both full |
| app-09-legal-documents | 2 | 2 | 0 | full | 2 | 0 | full | both full |
| app-10-telecom-billing | 3 | 3 | 0 | full | 3 | 0 | full | both full |
| app-11-social-analytics | 3 | 3 | 0 | full | 3 | 0 | full | both full |
| app-12-crypto-wallet | 3 | 3 | 0 | full | 3 | 0 | full | both full |
| app-13-project-mgmt | 3 | 3 | 0 | full | 3 | 0 | full | both full |
| app-14-telemedicine | 2 | 2 | 0 | full | 2 | 0 | full | both full |
| app-15-digital-assets | 2 | 2 | 0 | full | 0 | 2 | missed, rc=1, no report | Qwen |
| app-16-restaurant-reviews | 2 | 2 | 0 | full | 2 | 0 | full | both full |
| app-17-iot-dashboard | 2 | 2 | 0 | full | 2 | 0 | full | both full |
| app-18-p2p-lending | 2 | 2 | 0 | full | 2 | 0 | full | both full |
| app-19-cms | 2 | 2 | 0 | full | 2 | 0 | full | both full |
| app-20-fitness-tracker | 2 | 2 | 0 | full | 2 | 0 | full | both full |
| app-21-insurance-claims | 3 | 3 | 0 | full | 0 | 3 | missed, rc=1, no report | Qwen |
| app-22-food-delivery | 2 | 2 | 0 | full | 2 | 0 | full | both full |
| app-23-govt-permits | 2 | 0 | 2 | missed, rc=1, no report | 2 | 0 | full | Gemma-requested |
| app-24-vet-clinic | 3 | 3 | 0 | full | 3 | 0 | full | both full |
| app-25-supply-chain | 2 | 2 | 0 | full | 2 | 0 | full | both full |
| app-26-pharma-tracking | 2 | 2 | 0 | full | 2 | 0 | full | both full |
| app-27-hotel-reservation | 2 | 2 | 0 | full | 2 | 0 | full | both full |
| app-28-mfg-quality | 3 | 3 | 0 | full | 3 | 0 | full | both full |
| app-29-fleet-management | 2 | 2 | 0 | full | 2 | 0 | full | both full |
| app-30-auction-platform | 2 | 2 | 0 | full | 2 | 0 | full | both full |
| app-31-event-ticketing | 2 | 2 | 0 | full | 2 | 0 | full | both full |
| app-32-support-tickets | 2 | 2 | 0 | full | 2 | 0 | full | both full |
| app-33-recruitment-ats | 2 | 2 | 0 | full | 2 | 0 | full | both full |
| app-34-subscription-box | 2 | 2 | 0 | full | 2 | 0 | full | both full |
| app-35-compliance-tracker | 2 | 2 | 0 | full | 0 | 2 | missed, no report | Qwen |
| app-36-parking-mgmt | 2 | 2 | 0 | full | 2 | 0 | full | both full |
| app-37-crop-planner | 2 | 2 | 0 | full | 2 | 0 | full | both full |
| app-38-museum-catalog | 2 | 2 | 0 | full | 2 | 0 | full | both full |
| app-39-wedding-planner | 2 | 2 | 0 | full | 2 | 0 | full | both full |
| app-40-pet-adoption | 2 | 2 | 0 | full | 2 | 0 | full | both full |
| app-41-library-reservation | 2 | 2 | 0 | full | 2 | 0 | full | both full |
| app-42-construction-tracker | 2 | 2 | 0 | full | 2 | 0 | full | both full |
| app-43-music-streaming | 2 | 0 | 2 | missed, rc=1, no report | 2 | 0 | full | Gemma-requested |
| app-44-election-polling | 2 | 2 | 0 | full | 2 | 0 | full | both full |
| app-45-travel-expense | 2 | 2 | 0 | full | 2 | 0 | full | both full |
| app-46-charity-donations | 3 | 3 | 0 | full | 3 | 0 | full | both full |
| app-47-smart-home | 3 | 3 | 0 | full | 3 | 0 | full | both full |
| app-48-freelancer-market | 2 | 2 | 0 | full | 2 | 0 | full | both full |
| app-49-sports-league | 3 | 0 | 3 | missed, no report | 3 | 0 | full | Gemma-requested |
| app-50-energy-billing | 2 | 2 | 0 | full | 2 | 0 | full | both full |

## Project-by-Project Runtime, Calls, Tokens, And Cost

Token columns are `input/output/total`. Time is benchmark app wall-clock. Cost is the proxy-reported sum for requests attributed to that app window.

| Project | Qwen time | Qwen LLM calls | Qwen tokens | Qwen cost | Gemma time | Gemma LLM calls | Gemma tokens | Gemma cost |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| app-01-ecommerce-catalog | 1m 49s | 12 | 128,285/15,043/143,328 | $0.0335 | 51s | 8 | 63,790/6,742/70,532 | $0.0160 |
| app-02-patient-portal | 1m 14s | 10 | 96,465/10,019/106,484 | $0.0240 | 1m 30s | 10 | 97,342/10,933/108,275 | $0.0250 |
| app-03-banking-service | 1m 59s | 15 | 156,687/17,679/174,366 | $0.0403 | 2m 43s | 28 | 345,580/21,770/367,350 | $0.0725 |
| app-04-real-estate | 1m 45s | 13 | 164,617/13,051/177,668 | $0.0371 | 3m 45s | 17 | 208,247/21,007/229,254 | $0.0512 |
| app-05-learning-mgmt | 1m 15s | 8 | 47,523/9,524/57,047 | $0.0162 | 1m 7s | 8 | 49,045/9,020/58,065 | $0.0159 |
| app-06-hr-management | 1m 22s | 12 | 183,161/7,185/190,346 | $0.0343 | 32s | 10 | 87,316/3,738/91,054 | $0.0166 |
| app-07-airline-booking | 4m 31s | 30 | 471,445/31,269/502,714 | $0.1004 | 1m 19s | 8 | 139,281/9,869/149,150 | $0.0303 |
| app-08-warehouse-mgmt | 3m 5s | 38 | 533,384/24,028/557,412 | $0.1028 | 3m 12s | 18 | 413,243/26,168/439,411 | $0.0868 |
| app-09-legal-documents | 1m 36s | 13 | 116,733/12,082/128,815 | $0.0290 | 50s | 8 | 75,750/5,929/81,679 | $0.0170 |
| app-10-telecom-billing | 1m 50s | 15 | 120,488/17,955/138,443 | $0.0351 | 54s | 11 | 62,902/7,754/70,656 | $0.0168 |
| app-11-social-analytics | 2m 1s | 21 | 184,028/14,506/198,534 | $0.0414 | 3m 58s | 58 | 905,366/30,846/936,212 | $0.1651 |
| app-12-crypto-wallet | 1m 38s | 11 | 122,229/9,804/132,033 | $0.0276 | 52s | 9 | 46,069/8,128/54,197 | $0.0146 |
| app-13-project-mgmt | 2m 5s | 11 | 110,052/13,918/123,970 | $0.0297 | 1m 35s | 14 | 130,091/14,562/144,653 | $0.0333 |
| app-14-telemedicine | 1m 18s | 7 | 112,409/10,261/122,670 | $0.0266 | 31s | 5 | 17,209/5,113/22,322 | $0.0074 |
| app-15-digital-assets | 1m 39s | 9 | 54,643/11,270/65,913 | $0.0189 | 1m 6s | 13 | 87,725/9,976/97,701 | $0.0226 |
| app-16-restaurant-reviews | 1m 55s | 12 | 63,164/16,528/79,692 | $0.0252 | 41s | 6 | 23,126/6,449/29,575 | $0.0096 |
| app-17-iot-dashboard | 49s | 5 | 106,963/7,364/114,327 | $0.0230 | 50s | 8 | 52,176/8,038/60,214 | $0.0155 |
| app-18-p2p-lending | 1m 19s | 9 | 59,495/11,424/70,919 | $0.0198 | 1m 49s | 11 | 50,371/17,474/67,845 | $0.0242 |
| app-19-cms | 1m 0s | 9 | 46,633/7,344/53,977 | $0.0140 | 1m 7s | 9 | 45,198/10,061/55,259 | $0.0163 |
| app-20-fitness-tracker | 1m 10s | 10 | 137,599/10,212/147,811 | $0.0303 | 1m 24s | 10 | 114,228/7,752/121,980 | $0.0245 |
| app-21-insurance-claims | 1m 7s | 10 | 76,636/9,483/86,119 | $0.0205 | 1m 46s | 4 | 17,057/8,432/25,489 | $0.0106 |
| app-22-food-delivery | 1m 6s | 5 | 21,578/9,948/31,526 | $0.0127 | 2m 52s | 11 | 59,018/13,726/72,744 | $0.0219 |
| app-23-govt-permits | 56s | 6 | 21,775/9,253/31,028 | $0.0121 | 2m 47s | 7 | 31,363/12,303/43,666 | $0.0164 |
| app-24-vet-clinic | 53s | 6 | 25,267/8,443/33,710 | $0.0118 | 1m 7s | 4 | 16,834/4,906/21,740 | $0.0072 |
| app-25-supply-chain | 1m 39s | 19 | 132,945/16,841/149,786 | $0.0359 | 2m 11s | 11 | 45,564/8,706/54,270 | $0.0151 |
| app-26-pharma-tracking | 48s | 9 | 56,909/6,028/62,937 | $0.0143 | 1m 26s | 8 | 54,378/5,362/59,740 | $0.0133 |
| app-27-hotel-reservation | 56s | 8 | 49,047/7,536/56,583 | $0.0145 | 2m 21s | 12 | 71,253/10,626/81,879 | $0.0208 |
| app-28-mfg-quality | 1m 33s | 15 | 105,891/13,516/119,407 | $0.0287 | 1m 48s | 9 | 60,098/7,856/67,954 | $0.0165 |
| app-29-fleet-management | 1m 22s | 14 | 112,308/12,257/124,565 | $0.0285 | 1m 59s | 12 | 79,804/8,050/87,854 | $0.0196 |
| app-30-auction-platform | 1m 11s | 9 | 83,309/9,220/92,529 | $0.0213 | 1m 42s | 8 | 60,097/7,137/67,234 | $0.0158 |
| app-31-event-ticketing | 48s | 6 | 28,700/7,325/36,025 | $0.0113 | 1m 54s | 8 | 150,644/8,145/158,789 | $0.0303 |
| app-32-support-tickets | 1m 33s | 8 | 36,960/13,717/50,677 | $0.0186 | 1m 38s | 7 | 27,878/7,463/35,341 | $0.0113 |
| app-33-recruitment-ats | 1m 45s | 12 | 63,880/14,471/78,351 | $0.0233 | 2m 41s | 9 | 52,700/13,111/65,811 | $0.0204 |
| app-34-subscription-box | 33s | 7 | 31,212/4,349/35,561 | $0.0088 | 55s | 6 | 23,134/6,101/29,235 | $0.0093 |
| app-35-compliance-tracker | 2m 24s | 21 | 185,139/19,913/205,052 | $0.0467 | 3m 18s | 18 | 149,745/15,156/164,901 | $0.0369 |
| app-36-parking-mgmt | 1m 25s | 8 | 43,225/9,390/52,615 | $0.0154 | 37s | 6 | 22,842/4,889/27,731 | $0.0081 |
| app-37-crop-planner | 50s | 10 | 48,464/6,767/55,231 | $0.0137 | 1m 16s | 8 | 30,632/9,094/39,726 | $0.0132 |
| app-38-museum-catalog | 55s | 10 | 108,796/7,560/116,356 | $0.0235 | 1m 50s | 7 | 34,043/8,794/42,837 | $0.0135 |
| app-39-wedding-planner | 1m 0s | 7 | 46,655/8,714/55,369 | $0.0153 | 1m 6s | 7 | 30,421/5,565/35,986 | $0.0098 |
| app-40-pet-adoption | 1m 17s | 19 | 145,192/10,231/155,423 | $0.0315 | 2m 40s | 13 | 75,210/11,858/87,068 | $0.0225 |
| app-41-library-reservation | 51s | 7 | 94,902/8,403/103,305 | $0.0222 | 3m 34s | 13 | 83,897/15,025/98,922 | $0.0269 |
| app-42-construction-tracker | 1m 9s | 9 | 43,716/11,468/55,184 | $0.0175 | 2m 58s | 11 | 156,032/11,628/167,660 | $0.0345 |
| app-43-music-streaming | 1m 25s | 11 | 35,736/13,692/49,428 | $0.0184 | 2m 18s | 6 | 27,632/11,626/39,258 | $0.0152 |
| app-44-election-polling | 1m 17s | 12 | 55,617/12,329/67,946 | $0.0201 | 3m 55s | 16 | 115,888/18,867/134,755 | $0.0353 |
| app-45-travel-expense | 54s | 10 | 36,206/8,147/44,353 | $0.0132 | 1m 0s | 8 | 27,660/5,665/33,325 | $0.0095 |
| app-46-charity-donations | 1m 8s | 8 | 42,527/9,638/52,165 | $0.0155 | 2m 55s | 9 | 39,693/12,833/52,526 | $0.0181 |
| app-47-smart-home | 47s | 5 | 16,826/6,393/23,219 | $0.0086 | 2m 9s | 4 | 21,056/10,649/31,705 | $0.0133 |
| app-48-freelancer-market | 2m 46s | 24 | 140,893/21,865/162,758 | $0.0419 | 2m 17s | 16 | 106,387/17,258/123,645 | $0.0324 |
| app-49-sports-league | 1m 46s | 28 | 158,502/15,380/173,882 | $0.0384 | 2m 29s | 35 | 266,503/15,106/281,609 | $0.0543 |
| app-50-energy-billing | 51s | 6 | 56,194/7,606/63,800 | $0.0157 | 1m 16s | 5 | 31,062/8,969/40,031 | $0.0132 |

## Missed And Failed Projects

### Qwen

- `app-23-govt-permits`: missed; detected 0/2, missed 2. Expected chain: Debug Page Info Leak -> Unrestricted Upload -> RCE. Failure notes: returncode 1; no generated report; stderr: `Malformed JSON in tool arguments: Expecting property name enclosed in double quotes`.
- `app-43-music-streaming`: missed; detected 0/2, missed 2. Expected chain: Diagnostics Configuration Exposure -> SSRF Playlist Analytics Pivoting. Failure notes: returncode 1; no generated report; stderr: `Malformed JSON in tool arguments: Expecting property name enclosed in double quotes`.
- `app-49-sports-league`: missed; detected 0/3, missed 3. Expected chain: SQLi Player Dump -> IDOR Contract Access -> Score Manipulation. Failure notes: no generated report.

### Gemma-requested

- `app-06-hr-management`: missed; detected 0/3, missed 3. Expected chain: Credential Hash Harvest -> Offline Crack -> Payroll + SSN Exfiltration. Failure notes: no generated report.
- `app-15-digital-assets`: missed; detected 0/2, missed 2. Expected chain: SSRF File Fetch -> Predictable Path RCE. Failure notes: returncode 1; no generated report; stderr: `Malformed JSON in tool arguments: Expecting property name enclosed in double quotes`.
- `app-21-insurance-claims`: missed; detected 0/3, missed 3. Expected chain: SQL Injection -> IDOR Claim Access -> Silent Payout Fraud. Failure notes: returncode 1; no generated report; stderr: `Malformed JSON in tool arguments: Expecting property name enclosed in double quotes`.
- `app-35-compliance-tracker`: missed; detected 0/2, missed 2. Expected chain: Dev Mode Config Leak -> Admin Document Retrieval Bypass. Failure notes: no generated report.

## Safety And Isolation

- Qwen: compromised apps 0/50; parent/absolute-path tool refs 0; removed-doc tool refs 0; unsafe tool calls 0; hygiene passed 50/50.
- Gemma-requested: compromised apps 0/50; parent/absolute-path tool refs 0; removed-doc tool refs 0; unsafe tool calls 0; hygiene passed 50/50.

## Interpretation

- Qwen is the better strict-recall result in this benchmark snapshot: it solved one more app and recovered three more issue components overall.
- The Gemma-requested run was cheaper and used fewer LLM calls/tokens, but it had lower recall and longer wall-clock time. Its misses were concentrated in apps where the model either produced malformed tool JSON or exited with no report.
- The two runs are complementary at the app level. Qwen solved four apps the Gemma-requested run missed, while the Gemma-requested run solved three apps Qwen missed.
- The most important next step is not model tuning but validation of proxy routing for run 8. If `upstream_model` is authoritative, the Gemma-requested run was served by Qwen upstream and the benchmark should be rerun after pinning the provider route.
- After routing is confirmed, the biggest quality improvements are structured tool-call robustness, mandatory report emission on no-findings/low-confidence exits, and retry handling for malformed JSON failures.

## Exact Benchmark Command Shape

The command below was used per app, with only the model id differing between runs:

```powershell
<repo>\.venv\Scripts\cgopher.exe --events --no-project-init --approval-mode yolo --model <MODEL> --base-url http://LOCAL_LLM_HOST:8080/v1 --api-family chat_completions --replay-reasoning-content -p "Use @skill:chained-vulnerability-static-audit to perform a static-only chained vulnerability review of this codebase. Inspect only the current working directory. Do not use live probes, dynamic scanners, shell commands, or files outside this workspace. Write the final report with write_chained_vulnerability_report to docs/security/CHAINED_VULNERABILITIES_REVIEW.md."
```

## Source Artifacts

- Joined machine-readable comparison data: `<repo>\docs\plans\v0.8\report\20260525-195911-model-comparison\comparison-data.json`
- Qwen all-50 report: `<repo>\docs\plans\v0.8\report\20260524-234855-all50\REPORT.md`
- Gemma-requested all-50 report: `<repo>\docs\plans\v0.8\report\20260525-180047-gemma-all50\REPORT.md`

