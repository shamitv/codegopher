

## Audit Complete

I've completed the static-only chained vulnerability review and written the full report to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`.

### 🔍 3 Chained Vulnerabilities Found

| # | Severity | Chain |
|---|---|---|
| 1 | **HIGH** | **Admin Export via Info Disclosure** — `/api/system/health?diagnostics=true` leaks a hardcoded admin token; `/api/admin/export` uses that same token with no auth middleware → full database exfiltration |
| 2 | **MEDIUM** | **SQL Injection via Search** — `/api/tickets/search` uses string concatenation for `LIKE` queries → authenticated users can read/modify all database tables (including password hashes) |
| 3 | **LOW** | **Stack Trace & Query Leak** — `/api/tickets/:id` returns `err.stack` and raw queries in 500 responses → aids reconnaissance and targeted attacks |

### 📋 7 Cross-Cutting Weaknesses

- **WC-1:** `Math.random()` for session IDs (unpredictable)
- **WC-2:** CORS `origin: true` + `credentials: true` (any origin can send cookies)
- **WC-3:** No CSRF protection on state-changing endpoints
- **WC-4:** No role/ownership checks on ticket endpoints (any user sees all tickets)
- **WC-5:** No password policy on registration
- **WC-6:** Hardcoded seed passwords and admin token in source code
- **WC-7:** No rate limiting on login/register

### 🛠️ Key Remediation Priorities

1. **Remove `?diagnostics=true` in production** and never embed secrets in source
2. **Parameterize all SQL queries** (especially the search endpoint)
3. **Add proper auth middleware + RBAC** to `/api/admin/export`
4. **Use `crypto.randomBytes()`** for session IDs
5. **Restrict CORS** to known origins, add CSRF tokens
6. **Remove stack traces** from all error responses

The `referenceGuards.ts` file defines useful utility functions (`sameOwner`, `allowedCallback`, `normalizeIdentifier`) that are never imported or used — dead code that should either be wired into the app or removed.
