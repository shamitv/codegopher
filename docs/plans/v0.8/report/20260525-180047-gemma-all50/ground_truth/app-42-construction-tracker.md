# Ground Truth - app-42-construction-tracker

- App key: `app-42-construction-tracker`
- Source path: `D:\work\secure-code-hunt\apps\javascript\app-42-construction-tracker`
- Language/framework: javascript / express

## Expected Chained Attacks

### IDOR Information Mining → Insecure Deserialization Remote Code Execution

- Chain ID: `chain-01`
- Impact: account_takeover
- Scenario: An attacker logs in, retrieves construction contract details by calling `/api/contracts/1` (IDOR), and copies details. They then POST a template config to `/api/contracts/template` containing a system command execution payload (such as `require('child_process').execSync(...)`) evaluated unsafely via eval(), achieving Remote Code Execution.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A01 | medium | `src/index.js` | `GET /api/contracts/:id` | Contracts endpoint permits IDOR details mining. |
| 2 | A08 | medium | `src/index.js` | `POST /api/contracts/template` | Template processing executes user-submitted custom layouts via eval(). |
