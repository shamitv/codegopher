# Ground Truth - app-42-construction-tracker

- App key: `app-42-construction-tracker`
- Source path: `<secure-code-hunt>\apps\javascript\app-42-construction-tracker`
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

### Subtle State Confusion Pivot To Idor

- Chain ID: `chain-02`
- Impact: account_takeover
- Scenario: Attacker combines a low-visibility entry point with stored or derived application state, then pivots to a higher-impact sink that is reachable only after following the cross-file flow.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A09 | low | `src/index.js` | `POST /api/contracts/:id/delete` | Deleting sensitive construction contracts from the system tracker produces no audit logs, blindfolding administrators to data removal. |
| 2 | A08 | high | `src/index.js` | `POST /api/contracts/template` | Template layout parameters are deserialized using the insecure eval() constructor, enabling remote code execution on the hosting server. |
| 3 | A01 | medium | `src/index.js` | `GET /api/contracts/:id` | Viewing project contracts by ID lacks verification of user ownership, allowing any authenticated user to retrieve details of another manager's contracts. |
