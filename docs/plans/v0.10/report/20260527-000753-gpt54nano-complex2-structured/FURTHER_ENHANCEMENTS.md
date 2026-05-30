# Further Enhancements From Structured Run Delta

## Selection Rule Result

| Rule | Observed result | Selected follow-up |
|---|---|---|
| If line-reference coverage is below 75%, further strengthen line-numbered evidence collection | Reports had line references in both apps, and component file/symbol evidence reached 9/12 = 75.0% | No immediate line-numbering-only fix |
| If full-chain recall is below 75%, strengthen corrective second-pass criteria | Full-chain recall was 2/4 = 50.0% | Yes |
| If decoy misfires remain nonzero, refine evaluator/skill decoy language | Decoy misfires were 0 | No immediate decoy fix |
| If unmatched candidate chains remain high, improve report schema/title normalization | Unmatched candidate chains increased to 6 | Yes |

## Ranked Remaining Gaps

1. **Full-chain completion remains weak on helper/prerequisite evidence.**
   - Airline found important controller and SQL pieces but missed `PnrGenerator.generate` and did not connect `BookingService.createBooking`.
   - Expected impact of fix: high.
   - Risk: medium, because broader prompting can add cost or noise.

2. **Structural gates can pass while semantic completeness is still weak.**
   - The corrective second pass did not run because the reports had line refs, a ledger, and complete-chain claims.
   - Expected impact of fix: high.
   - Risk: low to medium if triggered only on generic unresolved-evidence language.

3. **Model evidence and model conclusion can disagree.**
   - Warehouse cited all expected LDAP/inventory components, but its ledger downgraded or rejected the chain.
   - Expected impact of fix: medium.
   - Risk: medium, because forcing acceptance can increase false positives.

4. **Candidate headings are too noisy for evaluator comparison.**
   - Table headings such as "Chain #1 Table" and duplicate chain sections were counted as unmatched candidate chains.
   - Expected impact of fix: medium.
   - Risk: low.

5. **Proxy-reported cost can diverge from token-count expectations.**
   - Structured run used fewer tokens but reported slightly higher cost.
   - Expected impact of fix: low for detection quality.
   - Risk: low; reporting should simply keep cost and token metrics separate.

## Follow-Up Fixes To Implement Now

Selected fixes are generic and do not use app-specific expected vulnerabilities.

1. **Broaden the source-derived pre-pass for quiet helper evidence.**
   - Add an inventory category for identifier, token, reference, display, and generator helpers.
   - Include files/symbols containing terms such as `generate`, `generator`, `sequence`, `reference`, `token`, `code`, `pnr`, `display`, `summary`, and `raw`.
   - Keep the pre-pass source-only and compact.

2. **Strengthen corrective second-pass criteria.**
   - Trigger a generic corrective pass when a report contains unresolved-not-reviewed language such as "no audit of", "not reviewed", "missing proof", or "missing evidence" while also claiming complete chains.
   - The corrective prompt should ask the model to resolve quiet-helper prerequisites and either complete, downgrade, or explicitly reject the chain.
   - Do not mention manifests or expected vulnerabilities.

3. **Normalize candidate titles in the evaluator.**
   - Deduplicate normalized candidate headings.
   - Ignore obvious table/subsection headings such as "Chain #1 Table".
   - Keep unmatched candidate chains as analyst-review items, not precision/F1 claims.

## Not Selected Yet

- Additional decoy scoring changes: no current decoy misfires.
- Broader line-numbering enforcement: reports had line references and met the 75% evidence threshold.
- Full benchmark rerun after follow-up fixes: not selected because the user requested implementation after the measured delta, not another run.
