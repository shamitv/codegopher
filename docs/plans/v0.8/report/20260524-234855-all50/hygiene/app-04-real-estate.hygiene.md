# Hygiene - app-04-real-estate

- Passed: yes
- Removed evaluator files: 3
- Sanitized source hints: 8
- Residual source hints: 0

## Removed Evaluator Files

- `.vulns`
- `README.md`
- `scenarios.md`

## Sanitized Source Hints

- `app.py:1` removed-line: A10: Server-Side Request Forgery (SSRF) ---
- `static/css/main.css:237` removed-line: /* Cyber Sandbox Panels */
- `static/index.html:86` removed-visible-hint-line: <h2 style="font-family: var(--font-luxury); font-size: 14px; color: var(--primary); margin-bottom: 12px;">Holographic Layout Remote Downloader (A10)</h2>
- `static/index.html:92` removed-visible-hint-line: <div id="ssrfConsoleFeed" class="terminal-feed">SSRF Sandbox Idle. Enter a layout URL above...</div>
- `static/index.html:94` removed-visible-hint-line: 💡 <span style="color: var(--primary);">A10 SSRF target:</span> Try probing internal subnets or local interfaces like <code>http://127.0.0.1:8084/api/properties</code>!
- `static/index.html:100` removed-visible-hint-line: <h2 style="font-family: var(--font-luxury); font-size: 14px; color: var(--primary); margin-bottom: 12px;">Property Description Subprocess Analyzer (A03)</h2>
- `static/index.html:106` removed-visible-hint-line: <div id="osConsoleFeed" class="terminal-feed">OS Shell Sandbox Idle. Enter property file name...</div>
- `static/index.html:108` removed-visible-hint-line: 💡 <span style="color: var(--primary);">A03 shell exploit payload:</span> Try injecting shell operators like <code>realty_vault.txt; whoami</code>!

## Residual Source Hints

- None
