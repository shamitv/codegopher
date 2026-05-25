# Ground Truth - app-18-p2p-lending

- App key: `app-18-p2p-lending`
- Source path: `<secure-code-hunt>\apps\javascript\app-18-p2p-lending`
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

### Subtle State Confusion Pivot To Idor

- Chain ID: `chain-02`
- Impact: db_exfiltration
- Scenario: Attacker combines a low-visibility entry point with stored or derived application state, then pivots to a higher-impact sink that is reachable only after following the cross-file flow.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A04 | medium | `src/index.js` | `POST /api/loans/apply` | The loan application endpoint fails to validate interest rates, allowing negative or zero interest loan generation to bypass standard interest accrual rules. |
| 2 | A02 | medium | `src/index.js` | `initDb` | User account passwords are saved in plaintext format in the database, risking exposure in data dumps. |
| 3 | A01 | medium | `src/index.js` | `GET /api/contracts/:id` | Viewing loan contract agreements by ID lacks checking user ownership, allowing any authenticated borrower to view details of any other borrower's loan agreement. |
