

The chained vulnerability audit is complete. Here's a summary of findings:

## Audit Results

### 3 Chains Detected (All HIGH severity, HIGH confidence)

| # | Chain | Impact |
|---|---|---|
| 1 | **Predictable Sessions → Account Takeover** | `Math.random()` generates session IDs — anyone who can predict/briute-force the token impersonates any user |
| 2 | **IDOR + Data Exposure** | All event and guest endpoints lack `user_id` ownership checks — any authenticated user can read/write other users' events and guest PII |
| 3 | **Hardcoded Admin Credentials + MD5 → Privilege Escalation** | Admin plaintext password (`plannerSecure2026!`) stored in source; MD5 hashing is trivially reversible — any source-reader becomes a full admin |

### 5 Cross-Cutting Weaknesses
- CORS with `origin: true` + `credentials: true` reflects any origin, enabling cross-origin session abuse
- No CSRF protection on any state-changing endpoint
- Verbose error messages leak user-existence state
- No input validation on registration
- In-memory session store (no persistence)

### P0 Remediations
1. Replace `Math.random()` with `crypto.randomBytes()`
2. Replace MD5 with the already-installed `bcryptjs`; remove hardcoded credentials
3. Add `user_id` ownership checks to all event- and guest-scoped queries

Full report written to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md` with Mermaid attack graphs, line-level citations, and prioritized remediation guidance.
