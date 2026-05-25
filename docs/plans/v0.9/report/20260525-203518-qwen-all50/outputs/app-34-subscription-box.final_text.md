

The chained vulnerability static audit is complete. The report has been written to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`.

---

## Audit Summary

### 3 Chained Vulnerabilities Identified

**Chain 1 — CRITICAL: SQL Injection → Full Database Exfiltration**
- **Source:** `src/index.ts:120-122` — `/api/packages/search`
- **Mechanism:** User query param `q` is directly interpolated into a SQL string via template literal: `` `LIKE '%${queryParam}%'` ``. No parameterization, no validation.
- **Impact:** Complete read (and potentially write) of all tables — credentials, PII, subscription data.
- **Confidence:** HIGH

**Chain 2 — HIGH: Hardcoded Admin Credentials + Weak Hashing → Full Admin Takeover**
- **Source:** `src/index.ts:63-65` — Plaintext `adminpass2026` for `admin_agent` in seed data; MD5 hashing throughout (`crypto.createHash('md5')`)
- **Mechanism:** Plaintext passwords in source, unsalted MD5 (cryptographically broken, rainbow-table-vulnerable), no rate limiting on login
- **Impact:** Trivial admin takeover via source code exposure or brute force (1000+ guesses/sec)
- **Confidence:** HIGH

**Chain 3 — HIGH: Permissive CORS + No CSRF → Unauthorized Cross-Site Actions**
- **Source:** `src/index.ts:11` — `cors({ origin: true, credentials: true })`; no CSRF validation in `requireAuth` or endpoints
- **Mechanism:** Any site can send credentialed requests; session cookie sent automatically with cross-origin POST; endpoints accept them without token checks
- **Impact:** Attacker can modify victims' subscription statuses and profile data
- **Confidence:** MEDIUM

### 7 Cross-Cutting Weaknesses
Unused guard functions, verbose error exposure, sessions with no expiry, bcryptjs dependency present but never used, unsalted MD5, no rate limiting, in-memory DB with seed data on every start.

### P0 Remediations
1. Parameterize the search SQL query
2. Replace MD5 with bcrypt; remove hardcoded credentials; add salt + work factor
3. Restrict CORS origins, add CSRF tokens, set SameSite cookie attribute
