# Ground Truth - app-35-compliance-tracker

- App key: `app-35-compliance-tracker`
- Source path: `<secure-code-hunt>\apps\typescript\app-35-compliance-tracker`
- Language/framework: typescript / express

## Expected Chained Attacks

### Dev Mode Config Leak → Admin Document Retrieval Bypass

- Chain ID: `chain-01`
- Impact: account_takeover
- Scenario: An attacker sends a request to the debug endpoint `/api/admin/debug?dev=true` to leak the developer administration token `ADMIN-DEV-TOKEN-KEY-8871`. Using this token in the `x-admin-token` header, the attacker authenticates as admin and accesses `/api/documents/1` to view sensitive customer compliance documents.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A05 | medium | `src/index.ts` | `GET /api/admin/debug` | Development debug settings leak administration API key. |
| 2 | A01 | medium | `src/index.ts` | `GET /api/documents/:id` | Documents details retrieval allows the attacker authenticated with the leaked API key to fetch arbitrary documents. |

### Subtle Deserialization Pivot To Idor

- Chain ID: `chain-02`
- Impact: account_takeover
- Scenario: Attacker combines a low-visibility entry point with stored or derived application state, then pivots to a higher-impact sink that is reachable only after following the cross-file flow.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A08 | high | `src/index.ts` | `POST /api/documents` | Document metadata is deserialized using the insecure eval() function, allowing execution of arbitrary system code via malicious metadata input. |
| 2 | A05 | medium | `src/index.ts` | `GET /api/admin/debug` | The debug endpoint leaks process environment details and a hardcoded administrative recovery API token when dev parameter is supplied. |
| 3 | A01 | medium | `src/index.ts` | `GET /api/documents/:id` | Retrieving document details by ID from the database fails to verify if the requesting user owns the document or possesses administrative permissions, allowing unauthorized access to arbitrary documents. |
