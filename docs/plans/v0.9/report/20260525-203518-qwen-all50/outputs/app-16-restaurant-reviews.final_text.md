

The chained vulnerability audit is complete. Here's what was found:

### 3 Chained Vulnerabilities Detected

1. **Critical — SQL Injection → Full Database Exfiltration** (Chain #1)
   - The restaurant search endpoint (`/api/restaurants/search?q=...`) uses string interpolation to build SQL queries, allowing UNION-based injection to read any table including the `users` table with password hashes.

2. **High — Broken Access Control on Review Edit** (Chain #2)
   - Any authenticated user can edit any review because the `sameOwner()` guard in `referenceGuards.js` is defined but **never imported or called** in the actual route handler.

3. **Critical — Predictable Sessions + CORS Misconfiguration → Full Account Takeover** (Chain #3)
   - Session IDs are generated with `Math.random()` (not CSPRNG), CORS is set with `origin: true, credentials: true` (accepts any origin with credentials), and no CSRF protection exists. Together, these allow an attacker to hijack admin sessions or perform cross-origin attacks.

### 5 Cross-Cutting Weaknesses
- Hardcoded credentials in seed data, verbose error messages exposing internal errors, in-memory session store with no expiration, no rate limiting on auth endpoints, and no CSP headers.

The full report has been written to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`.
