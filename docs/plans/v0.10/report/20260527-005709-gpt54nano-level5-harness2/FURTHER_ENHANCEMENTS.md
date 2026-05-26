# Further Enhancements From Level-5 Delta

## Selection Rule Result

| Rule | Observed result | Selected follow-up |
|---|---|---|
| If exact-evidence coverage is below 75%, strengthen evidence parser/gates | 21/98 = 21.4% | Yes |
| If full-chain recall is below 75%, strengthen bounded review triggers | 9/11 = 81.8% | No |
| If safe-control misclassification is nonzero, improve same-path guard handling | Safe-control class labels were often omitted or parsed as unknown | Yes |
| If unmatched candidates are high, improve ledger/title normalization | 8 unmatched headings across 9 apps | Yes |
| If token cost per completed chain worsens materially, tighten pre-pass caps and ranking | Expanded-scope cost rose, but per-app cost stayed close to prior baseline | No immediate cost fix |

## Selected Follow-Up Fixes

1. **Parse nested ledger evidence objects.**
   - The model often emitted `source: { evidence: { ... } }` or `hop: { evidence: [ ... ] }`.
   - The parser should count those nested evidence objects when they contain full path, symbol, and line/range fields.

2. **Strengthen safe-control classification.**
   - Prompt and skill guidance should require each safe control to use one of: `same_path_blocker`, `nearby_only`, `not_applicable`, or `unknown`.
   - The corrective gate should trigger when safe controls exist but all classifications remain unknown.

3. **Normalize generic chain headings.**
   - Ignore generic headings such as `Chain details`.
   - Keep real unmatched chain candidates visible for analyst review, but do not count report-section labels as candidate chains.

## Not Selected

- More broad search or additional corrective passes: recall is above the threshold, and all apps already used one corrective pass.
- More decoy scoring changes: decoy misfires stayed at zero.
- Pre-pass cost reduction: cost increased mainly because the scope expanded from two apps to nine apps.

## Expected Impact

These fixes should improve measured evidence quality and report consistency without overfitting to the benchmark apps. They do not use manifests in prompts and do not add any public CLI behavior.
