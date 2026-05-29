# Improvement Opportunities From Implemented Complexity-App Runs

- Stamp: `20260528-224739`
- Basis: six model runs across seven implemented complexity-upgrade apps.
- Goal: general CodeGopher improvements, not tuning for any single app.

## Priority Opportunities

### 1. Separate Recall Repair From Ledger Repair

DeepSeek and Qwen found more expected chain components than the other models, but ledger validity lagged. CodeGopher should run an explicit final ledger repair pass when recall signals are strong but the structured ledger is invalid or incomplete.

- Impact: high
- Effort: medium
- Risk: low
- Validation: add benchmark assertions for valid ledger plus high-recall cases, then re-run two languages.

### 2. Make Episodic State Drive Corrective Passes

Most models needed corrective passes on most apps. The corrective prompt should receive a compact episode state: inspected files, candidate sources, hops, sinks, rejected controls, missing evidence, and remaining TODOs.

- Impact: high
- Effort: medium
- Risk: medium
- Validation: compare attempt count, recall, and ledger validity before and after on at least one Python, one Java, and one TypeScript app.

### 3. Add Early Chain-Synthesis Checkpoints

Several scans completed discovery but still missed full chains. Add a mid-run checkpoint that requires at least one source-hop-sink candidate per reviewed high-risk family before final report writing.

- Impact: high
- Effort: medium
- Risk: medium
- Validation: verify fewer shallow no-chain reports and no increase in unsafe file access.

### 4. Improve Cost-Aware Model Control

Qwen produced strong recall but with the highest cost, tokens, retries, and wall time. GPT 5.4 Mini was fastest but costlier than Nano and Gemma at lower token volume. Add optional benchmark cost ceilings, per-app timeout summaries, and partial-result preservation.

- Impact: medium
- Effort: low
- Risk: low
- Validation: simulate budget ceiling and confirm proxy runs close cleanly with sanitized partial summaries.

### 5. Track Retry Causes As First-Class Metrics

Qwen had four transient retry apps and DeepSeek had one. The benchmark should categorize retry triggers: provider error, malformed output, timeout, missing final report, or quality-gate failure.

- Impact: medium
- Effort: low
- Risk: low
- Validation: unit-test retry classification and include it in model comparisons.

### 6. Strengthen Discovery Coverage Signals

Recall did not always track discovery-complete status. Add stricter checks that discovered routes, workers, policy checks, serializers, query builders, token/session logic, and outbound calls are connected into candidate flows instead of only being visited.

- Impact: medium
- Effort: medium
- Risk: medium
- Validation: require candidate flow coverage in benchmark summaries without exposing private scoring content.

### 7. Add A Composite Quality Score

The current report has recall, ledger validity, evidence quality, safety, and cost as separate dimensions. Add a composite score for model comparison that weights complete-chain recall, component recall, valid ledger, evidence exactness, safety, and cost.

- Impact: medium
- Effort: low
- Risk: low
- Validation: snapshot-test score calculations and confirm rankings remain explainable.

## Suggested Next Validation

- Re-run a smaller three-model set after implementing ledger repair and episode-driven correction.
- Include one app per language to verify the changes generalize.
- Keep raw artifacts outside committed docs and commit only aggregate sanitized summaries.
