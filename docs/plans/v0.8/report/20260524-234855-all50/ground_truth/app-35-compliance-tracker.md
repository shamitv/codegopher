# Ground Truth - app-35-compliance-tracker

- App key: `app-35-compliance-tracker`
- Source path: `D:\work\secure-code-hunt\apps\typescript\app-35-compliance-tracker`
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
