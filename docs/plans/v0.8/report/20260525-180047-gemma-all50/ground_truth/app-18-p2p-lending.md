# Ground Truth - app-18-p2p-lending

- App key: `app-18-p2p-lending`
- Source path: `D:\work\secure-code-hunt\apps\javascript\app-18-p2p-lending`
- Language/framework: javascript / express

## Expected Chained Attacks

### Plaintext Credential Leak → IDOR Loan Data Harvesting

- Chain ID: `chain-01`
- Impact: db_exfiltration
- Scenario: An attacker reads plaintext credentials from a debug configuration or database leak at `/api/debug/users` to get admin passwords (`lenderSecure2026!`). Authenticating with the admin credentials, the attacker invokes the loan details endpoint `/api/contracts/1` and extracts private borrower financial contract details via IDOR.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A02 | medium | `src/index.js` | `initDb` | Plaintext credentials leak from user profile queries. |
| 2 | A01 | medium | `src/index.js` | `GET /api/contracts/:id` | Contracts endpoint permits IDOR fetching of arbitrary records. |
