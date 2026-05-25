

The chained vulnerability static audit is complete. Here's a summary of the findings:

### Chains Identified: 3

| Chain | Severity | Confidence | Description |
|---|---|---|---|
| **1** | **CRITICAL** | High | **IDOR → Private Key Theft → Full Wallet Control**. The `GET /api/wallet?userId=X` endpoint has no ownership check, allowing any authenticated user to read any other user's wallet — including plaintext private keys — which are also displayed on the frontend dashboard. |
| **2** | **CRITICAL** | High | **Hardcoded Plaintext Credentials → Universal Account Takeover**. All user passwords are stored in plaintext in `src/db.ts` and compared with direct string equality. Combined with predictable session IDs (just the user's numeric ID), source code access equals full account compromise. |
| **3** | **HIGH** | High | **Missing Ownership Verification on External Transfer**. The `POST /api/wallet/external-transfer` endpoint accepts `fromAddress` from the request body with no ownership proof, allowing authenticated attackers to drain any known wallet without the private key. |

### Key Cross-Cutting Weaknesses
- No CSRF protection, no rate limiting, no HTTPS/TLS
- Private keys rendered in plaintext on the browser UI
- `sameSite: 'lax'` and no `secure` flag on session cookies
- Orphaned code block in `wallet.service.ts` (missing function declaration)

The full report has been written to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md` with Mermaid attack graphs, detailed code references, line numbers, remediation guidance, and prioritized fix recommendations.
