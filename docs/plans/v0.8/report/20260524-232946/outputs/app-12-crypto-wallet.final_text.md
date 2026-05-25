

The **Chained Vulnerability Static Audit** is complete. Here's a summary of what was found:

---

## Audit Results

### 4 Attack Chains Identified

| # | Chain | Severity | Key Mechanism |
|---|---|---|---|
| **1** | **IDOR + Private Key Leakage** → Full wallet compromise via on-chain transfer | **HIGH** | `GET /api/wallet?userId=<victim_id>` returns the entire wallet object including the private key — no ownership check |
| **2** | **IDOR + Missing Ownership Verification** → Fund theft without private key | **HIGH** | `POST /api/wallet/external-transfer` accepts a `fromAddress` from the request body with zero verification that the authenticated user owns it |
| **3** | **Plaintext Passwords + No Rate Limiting** → Account takeover via brute force | **HIGH** | Passwords compared in plaintext against static array; no throttling on login |
| **4** | **Source Code Exposure** of private keys & credentials | **CRITICAL** | Full Ethereum private keys and plaintext passwords hardcoded in `src/db.ts` — anyone with repo access can drain all wallets |

### 8 Cross-Cutting Weaknesses

No CSRF tokens, no CORS configuration, no security headers, no address validation, no HTTPS enforcement, no audit logging, no replay protection, and session IDs are just predictable user IDs.

### Top Remediation Actions
- **P0:** Remove private keys from source; rotate all exposed keys immediately
- **P1:** Hash passwords, add rate limiting, filter `privateKey` from API responses
- **P1:** Enforce `targetUserId === user.id` and add ownership verification on `external-transfer`

The full report has been written to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`.
