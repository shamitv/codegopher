

The chained vulnerability static audit is complete. Here's a summary of what was found and written to the report:

## Audit Results — Fitness Tracker API (`src/index.js`)

### 3 Chains Detected

| # | Severity | Chain |
|---|---|---|
| 1 | **HIGH** | **Prototype Pollution → Privilege Escalation** — The `unsafeMerge()` function at lines 126-135 has no `hasOwnProperty` guard, allowing `__proto__` injection via `POST /api/user/settings`. This can corrupt `Object.prototype` and, if settings are re-merged into session/user objects, inflate roles to `ADMIN`. |
| 2 | **MEDIUM** | **Weak Session Generation + No CSRF → Account Takeover** — Session IDs use `Math.random()` (not CSPRNG) at lines 113-114, making them predictable. Combined with missing CSRF protection on `POST /api/user/settings`, an attacker can forge requests using the victim's cookies. |
| 3 | **LOW** | **Hardcoded Seed Passwords + No Rate Limiting → Brute-Force Takeover** — Three seed users (including `admin_coach`) have plain-text passwords hardcoded in source at lines 45-50. The login endpoint has no rate limiting, enabling rapid brute-force. |

### 5 Cross-Cutting Weaknesses
- Permissive CORS (`origin: true` + `credentials: true`)
- No role-based access control despite role field existing
- No input validation on route params
- Verbose error message inconsistency
- In-memory database (no persistence)

The full report has been written to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`.
