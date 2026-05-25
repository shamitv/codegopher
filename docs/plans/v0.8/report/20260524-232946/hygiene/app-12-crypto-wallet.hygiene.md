# Hygiene - app-12-crypto-wallet

- Passed: yes
- Removed evaluator files: 3
- Sanitized source hints: 4
- Residual source hints: 0

## Removed Evaluator Files

- `.vulns`
- `README.md`
- `scenarios.md`

## Sanitized Source Hints

- `public/index.html:3` removed-visible-hint-line: <div style="font-size: 11px; color: var(--danger); text-transform: uppercase; font-weight: 700; margin-bottom: 8px;">⚠️ CRITICAL SECURITY WARNING (A02 VISUALIZER)</div>
- `public/index.html:45` removed-visible-hint-line: <div style="font-size: 11px; color: var(--primary); text-transform: uppercase; font-weight: 700; margin-bottom: 4px;">Security Analysis (A04 & A07)</div>
- `public/index.html:46` removed-visible-hint-line: <p style="font-size: 12px; color: var(--text-muted); line-height: 1.5;">Clicking "Execute Transfer" will immediately deduct funds. There is <strong>no transaction confirmation step (A04)</strong> and <strong>no Multi-Fac
- `src/wallet/wallet.controller.ts:36` removed-line: // Vulnerable: no ownership check — fromAddress not verified against req['user']

## Residual Source Hints

- None
