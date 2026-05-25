

The chained vulnerability static audit is complete. Here's a summary of findings:

## Report Written: `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`

### 4 Attack Chains Identified

| # | Chain | Severity | Confidence |
|---|-------|----------|------------|
| 1 | **SQL Injection → Full DB Exfiltration** (unparameterized query in `/api/restaurants/search`) | HIGH | HIGH |
| 2 | **Hardcoded Credentials → Admin Access** (plaintext admin password in source) | HIGH | HIGH |
| 3 | **Predictable Sessions + IDOR → Unauthorized Review Edit** (`Math.random()` sessions, no ownership check) | MEDIUM | MEDIUM |
| 4 | **SQLi Error Leak → Schema Disclosure** (verbose `err.message` in error response) | MEDIUM | HIGH |

### Key Sources of the Chains

- **Line 136** — `LIKE '%${queryParam}%'` — raw string interpolation in SQL → Chain 1 & 4
- **Lines 55-57** — `admin_critic: critic2026Secure!` hardcoded → Chain 2
- **Line 115** — `Math.random()` for session IDs → Chain 3
- **Lines 157-169** — `UPDATE reviews SET ... WHERE id = ?` without ownership validation → Chain 3
- **Line 138** — `details: err.message` leaked to client → Chain 4

### Cross-Cutting Weaknesses

No CSRF protection, no rate limiting, permissive CORS (`origin: true` + `credentials: true`), missing session expiration/Secure flags, no input validation on rating values, and missing `npm audit`.

### Top 3 Remediations (Easiest to implement)

1. **Parameterize the search query** (`src/index.js:136`) — breaks 2 chains
2. **Remove hardcoded admin credentials** (`src/index.js:51-57`) — breaks 1 chain
3. **Add ownership check** in review edit handler (`src/index.js:157-169`) — breaks 1 chain
