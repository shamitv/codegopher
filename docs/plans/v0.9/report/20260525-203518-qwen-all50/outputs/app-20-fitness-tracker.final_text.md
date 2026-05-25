

The chained vulnerability static audit is complete. Here's a quick summary of what was found:

## Audit Complete ✅

**Report written to**: `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`

### 4 Chains Detected

| # | Chain | Severity | Key Finding |
|---|-------|----------|-------------|
| 1 | **IDOR on `/api/activities/:id`** | 🔴 HIGH | Authenticated users can read any activity record — the single-activity endpoint filters by `id` only, never checking `user_id` ownership |
| 2 | **CORS + Missing CSRF** | 🟡 MEDIUM | `cors({ origin: true, credentials: true })` reflects any origin while sending cookies, enabling cross-origin state changes |
| 3 | **Prototype Pollution via `/api/user/settings`** | 🟡 MEDIUM | `unsafeMerge()` accepts raw `req.body.customSettings` with no `__proto__` guards, allowing global `Object.prototype` pollution |
| 4 | **Predictable Session IDs** | 🟢 LOW | `Math.random()` is not cryptographically secure; session IDs can potentially be predicted |

### 6 Cross-Cutting Weaknesses
- Hardcoded plaintext admin credentials in seed data
- No rate limiting on login/register
- No session expiration
- Verbose error leaking user enumeration info
- In-memory session store (no persistence)
- No Docker security hardening

### P0 Fix (Immediate)
Add `AND user_id = ?` to the `/api/activities/:id` query to block the HIGH-severity IDOR chain.
