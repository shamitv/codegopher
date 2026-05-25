

The chained vulnerability static audit is complete. The report has been written to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`.

## Audit Summary

### Chains Found: 5

| # | Chain | Severity | Confidence |
|---|---|---|---|
| 1 | **External-Transfer Bypass** — Any authenticated user can drain any wallet by specifying the victim's address as `fromAddress` on `POST /api/wallet/external-transfer`, with no ownership check in `executeTransferByAddress` | **CRITICAL** | High |
| 2 | **IDOR + Private Key Leakage** — `GET /api/wallet?userId=X` allows any authenticated user to fetch any other user's wallet including plaintext `privateKey`, which the frontend displays in the DOM | **CRITICAL** | High |
| 3 | **CSRF on Fund Transfer** — `POST /api/wallet/transfer` has no CSRF token validation; session cookie uses `sameSite: lax` without `secure: true`, enabling cross-site POST-based fund theft | **HIGH** | High |
| 4 | **Plaintext Passwords + No Rate Limit** — Passwords stored/compared in plaintext (`db.ts:4-5`) with zero throttling on `/api/auth/login`; cookie lacks `secure` flag, enabling offline brute force + session hijack | **HIGH** | High |
| 5 | **Private Key Echo to Client** — Server API returns full wallet object (including `privateKey`), which `app.js` writes directly to the DOM via `innerText` — exposed to DevTools, extensions, and screen captures | **MEDIUM** | High |

### Key Findings

- **`src/db.ts`** stores passwords in plaintext AND private keys in plaintext — the data model itself is the root weakness
- **`wallet.controller.ts`** explicitly acknowledges the IDOR flaw in a code comment (`getWallet` accepts arbitrary `userId`)
- **`wallet.service.ts`** has a truncated/malformed `executeTransferByAddress` method (the `function executeTransferByAddress(body.fromAddress...` declaration appears missing) that still processes transfers by address alone
- **Frontend (`app.js`)** renders private key in DOM, uses `innerHTML` for transaction rows (potential XSS vector), and has no CSRF token management
- **No rate limiting, no input validation beyond basic checks, and the `tsconfig.json` has most strictness flags disabled**

### 6 Cross-Cutting Weaknesses Identified

No rate limiting, insecure cookie flags, insufficient transfer validation, in-memory DB, relaxed TypeScript checks, and DOM-injection XSS risk.

**Priority P0 actions**: Remove `privateKey` from all API responses, add ownership checks to `executeTransferByAddress`, and add server-side authorization for the `GET /api/wallet` userId parameter.
