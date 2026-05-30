# Further Enhancements From Post-Follow-Up Delta

## Selection Rule Result

| Rule | Observed result | Selected follow-up |
|---|---|---|
| If line-reference coverage is below 75%, further strengthen line-numbered evidence collection | Strict component file+symbol evidence was 6/12 = 50.0%, despite 35 raw line refs | Yes |
| If full-chain recall is below 75%, strengthen corrective second-pass criteria | Full-chain recall was exactly 3/4 = 75.0% | No immediate full-chain recall fix by rule |
| If decoy misfires remain nonzero, refine evaluator/skill decoy language | Decoy misfires were 0 | No |
| If unmatched candidate chains remain high, improve report schema/title normalization | Unmatched candidates dropped to 2 | No immediate normalization fix |

## Ranked Remaining Gaps

1. **Exact evidence discipline is now the biggest blocker.**
   - Reports include line references, but not always the full relative path plus exact method/symbol in the same ledger row.
   - Expected impact of fix: high.
   - Risk: low.

2. **Quiet helper discovery is better but still incomplete.**
   - Airline still missed the `PnrGenerator.generate` prerequisite.
   - Expected impact of fix: medium.
   - Risk: medium if broad helper patterns add too much prompt noise.

3. **Conclusion consistency still needs a stronger self-check.**
   - Warehouse was scored full, but some report wording still marked related paths as incomplete or partially inferred.
   - Expected impact of fix: medium.
   - Risk: low.

4. **Cost increased.**
   - More tool/model calls improved recall but increased tokens and cost.
   - Expected impact of fix: low for quality.
   - Risk: low; report cost separately from recall.

## Follow-Up Fixes To Implement Now

Selected fixes are generic and do not use app-specific expected vulnerabilities.

1. **Strengthen exact evidence instructions.**
   - Require every final ledger row and source-hop-sink table row to cite the full repository-relative path, exact symbol/method name, and line or line range.
   - Explicitly forbid abbreviated filenames such as `BookingController.java:40-47` when the full path is known.
   - Tell the model to re-read source with line numbers if any row lacks exact path/symbol/line evidence.

2. **Tighten the source pre-pass helper category.**
   - Reduce broad domain nouns in the helper inventory that crowd out generator/helper classes.
   - Prioritize high-signal helper terms such as `generate`, `generator`, `sequence`, `token`, `reference`, `pnr`, `display`, `summary`, `raw`, `label`, and `receipt`.

3. **Add an evidence-gap corrective trigger.**
   - Trigger a corrective pass when a report has a ledger but uses abbreviated evidence patterns or has missing-path/missing-symbol wording.
   - The prompt should ask only for evidence completion, not a full audit restart.

## Not Selected Yet

- Additional decoy scoring changes: no current decoy misfires.
- More candidate-title normalization: unmatched candidates are lower and not the dominant gap.
- Another full benchmark rerun after these fixes: not selected unless explicitly requested.
