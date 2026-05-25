

The chained vulnerability audit is complete. Here's a summary of findings:

---

## Audit Complete — 4 Chains Detected

| Chain | Severity | Confidence | Title |
|-------|----------|------------|-------|
| 1 | **HIGH** | HIGH | Weak Session ID Generation + Missing CSRF → Session Hijack + Privilege Escalation |
| 2 | **HIGH** | HIGH | Hardcoded Admin Credentials + No Rate Limiting → Account Takeover |
| 3 | **MEDIUM** | HIGH | IDOR on Exhibit Detail → Confidential Data Exposure |
| 4 | **MEDIUM** | MEDIUM | Weak Sessions + IDOR + Wildcard CORS → Cross-User Data Exfiltration |

### Critical Findings

1. **`Math.random()` for session IDs** (`src/index.js:146`) — Not cryptographically secure. An attacker can predict/brute-force session tokens.
2. **Plaintext admin password in source** (`src/index.js:74`) — `curator_admin` / `curator2026Secure!` is hardcoded. Anyone with repo access has admin.
3. **No authorization on `GET /api/exhibits/:id`** (`src/index.js:160-170`) — Any authenticated user can read `confidential_notes` on any exhibit (including $5M insurance details and Level-3 security clearance).
4. **Wildcard CORS + no `sameSite`** (`src/index.js:11, 148`) — Any origin can make authenticated cross-origin requests, enabling cross-user data exfiltration.

### Easiest Fixes (Break the Chain)

1. Replace `Math.random()` with `crypto.randomBytes(32).toString('hex')` — one line, kills session prediction
2. Move passwords to environment variables — eliminates direct admin takeover
3. Add `sameSite: 'strict'` to cookie options — mitigates CSRF and cross-origin attacks
4. Add `req.user.role !== 'ADMIN'` ownership check on exhibit detail retrieval

### Report Written To

`docs/security/CHAINED_VULNERABILITIES_REVIEW.md`

The report includes Mermaid attack graphs for each chain, line-by-line evidence with source references, cross-cutting weaknesses (7 identified), unknowns with suggested tests, and prioritized remediation recommendations.
