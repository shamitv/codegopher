# Ground Truth - app-34-subscription-box

- App key: `app-34-subscription-box`
- Source path: `<secure-code-hunt>\apps\typescript\app-34-subscription-box`
- Language/framework: typescript / express

## Expected Chained Attacks

### Package Search SQLi → Unsalted MD5 Credential Cracking

- Chain ID: `chain-01`
- Impact: account_takeover
- Scenario: An attacker uses a SQL union injection query on `/api/packages/search?q=coffee' UNION SELECT 1,username,password_hash,role FROM users --` to dump the users table. They retrieve the unsalted MD5 hash `a57e4e138a08d3744952bd0176cd1f91` for the admin_agent user. By performing offline MD5 decryption/lookup, they crack the admin password ('adminpass2026') and take over the admin session.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A03 | medium | `src/index.ts` | `GET /api/packages/search` | Union-based SQL injection on package search exposes internal database tables. |
| 2 | A07 | medium | `src/index.ts` | `POST /api/auth/login` | Admin passwords stored as unsalted MD5 hashes are cracked offline, enabling account takeover. |

### Subtle State Confusion Pivot To Injection

- Chain ID: `chain-02`
- Impact: account_takeover
- Scenario: Attacker combines a low-visibility entry point with stored or derived application state, then pivots to a higher-impact sink that is reachable only after following the cross-file flow.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A09 | low | `src/index.ts` | `POST /api/subscriptions/update` | Critical security events such as subscription modifications or payment level updates are not logged, disabling security event visibility. |
| 2 | A07 | medium | `src/index.ts` | `POST /api/auth/login` | User account passwords are encrypted using unsalted MD5 hashing and saved in the database, allowing brute-force or rainbow table cracking. |
| 3 | A03 | high | `src/index.ts` | `GET /api/packages/search` | The search query parameter is directly concatenated into a raw SQL query statement, leading to SQL injection. |
