

The chained vulnerability audit is complete. Here's a summary of findings:

## Audit Results: 3 Chains Detected

### Chain 1 — SQL Injection (HIGH)
- **Entry:** `GET /api/packages/search` at `src/index.ts:142` — `req.query.q` is directly interpolated into a SQL string via template literals
- **Sink:** `db.all(sql, ...)` at line 143 — executes the unparameterized query
- **Impact:** Full read access to all database tables (users, packages, subscriptions)
- **Fix:** Use parameterized queries with `?` placeholders

### Chain 2 — SQL Injection + MD5 Weak Hash → Admin Takeover (CRITICAL)
- **Entry:** Same SQL injection as Chain 1
- **Hop 1:** MD5 hashing with no salt (`crypto.createHash('md5')`) at line 118
- **Hop 2:** Plaintext admin password `"adminpass2026"` hardcoded in seed data at line 50
- **Target:** Login at lines 117–130 — once credentials are known, full admin session is issued
- **Impact:** Complete account takeover of `admin_agent` with unrestricted operations
- **Fix:** Migrate to bcrypt (already a dependency), remove hardcoded credentials, use env vars

### Chain 3 — Permissive CORS + No CSRF → Cross-Origin State Manipulation (MEDIUM)
- **Entry:** `cors({ origin: true, credentials: true })` at line 10 — allows any origin to read responses with credentials
- **Gap:** No CSRF token validation on any POST endpoint (register, login, logout, subscriptions, profile)
- **Impact:** Attackers on controlled pages can read responses and manipulate authenticated user state
- **Fix:** Restrict CORS to specific origins; add CSRF token validation

### 6 Additional Cross-Cutting Weaknesses
Plaintext passwords in source, no rate limiting, verbose error exposure, role leakage in API responses, volatile in-memory DB, and unvalidated subscription status input.

The full report with Mermaid attack graphs has been written to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`.
