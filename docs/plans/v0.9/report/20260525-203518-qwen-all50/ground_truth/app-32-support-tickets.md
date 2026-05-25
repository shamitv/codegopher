# Ground Truth - app-32-support-tickets

- App key: `app-32-support-tickets`
- Source path: `<secure-code-hunt>\apps\typescript\app-32-support-tickets`
- Language/framework: typescript / express

## Expected Chained Attacks

### Verbose Diagnostics Exposure → Administrative Ticket Export Bypass

- Chain ID: `chain-01`
- Impact: db_exfiltration
- Scenario: An attacker queries the health diagnostics endpoint `/api/system/health?diagnostics=true` to leak the system configuration containing the hardcoded recovery key `SUPPORT-ADMIN-DEV-RECOVERY-KEY-2026`. The attacker then invokes the endpoint `/api/admin/export` passing this key in the `x-admin-token` header, enabling them to bulk export all tickets and users from the database.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A05 | medium | `src/index.ts` | `GET /api/system/health` | System diagnostics endpoint leaks secret admin recovery token. |
| 2 | A01 | medium | `src/index.ts` | `POST /api/admin/export` | Admin export endpoint allows data exfiltration by verifying only the leaked recovery key. |

### Subtle Auth Session Pivot To Idor

- Chain ID: `chain-02`
- Impact: db_exfiltration
- Scenario: Attacker combines a low-visibility entry point with stored or derived application state, then pivots to a higher-impact sink that is reachable only after following the cross-file flow.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A05 | medium | `src/index.ts` | `GET /api/system/health` | An endpoint exposes diagnostic info and verbose environment variables (including administrative recovery token and cookie secret) when requesting the system health status with diagnostic mode. |
| 2 | A03 | high | `src/index.ts` | `GET /api/tickets/search` | The search query parameter is directly concatenated into a raw SQL query statement, leading to SQL injection. |
| 3 | A01 | medium | `src/index.ts` | `GET /api/tickets/:id` | The ticket detail retrieval endpoint fails to verify if the requesting user owns the ticket or possesses admin permissions, allowing authenticated users to access arbitrary tickets. |
