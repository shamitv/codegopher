

The chained vulnerability static audit is complete. Here's a summary of what was found:

## Audit Results

**3 chained vulnerabilities** were identified across the Crypto Wallet Service codebase:

### Critical Chains

1. **IDOR + Private Key Exposure → Full Wallet Compromise** — The `GET /api/wallet?userId=N` endpoint allows any authenticated user to fetch any other user's wallet object (including the plaintext `privateKey`), which the SPA then displays in the DOM. No authorization check on `userId` is present.

2. **External-Transfer Auth Bypass → Arbitrary Fund Theft** — The `POST /api/wallet/external-transfer` endpoint accepts a `fromAddress` parameter but never verifies the authenticated session owns that address. The source code even contains a comment admitting this flaw. The service-side method `executeTransferByAddress` is orphaned code with a compile error but the design intent is clear.

### High Chain

3. **Plaintext Passwords + No Rate Limit → Brute Force → Account Takeover** — Passwords are stored in plaintext (`alice123`, `bob123`) in a hardcoded array, and the login endpoint has no throttling, enabling trivial brute-force attacks.

### Cross-Cutting Weaknesses

- No CSRF tokens on any POST endpoint
- Cookie `sameSite: 'lax'` (partial CSRF protection)
- No HTTPS/TLS configuration in Docker or bootstrap
- No CORS restrictions
- Orphaned/unreachable code in `WalletService`

The full report with Mermaid attack graphs, line-level evidence, and remediation priorities has been written to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`.
