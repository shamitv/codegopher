

The chained vulnerability static audit is complete. Here's a summary of what was found:

**Report written to:** `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`

## Key Findings

| Metric | Value |
|---|---|
| Chained vulnerabilities | **4** |
| Maximum severity | **CRITICAL** |
| Cross-cutting weaknesses | **6** |

### 4 Confirmed Chains

1. **C1 (CRITICAL)** — Unauthenticated `/health?diagnostics=true` returns the admin recovery token → attacker calls `/api/admin/export` to exfiltrate the entire database (tickets + user password hashes).

2. **C2 (CRITICAL)** — Authenticated user sends crafted `?q=` to `/api/tickets/search` → SQL injection via string interpolation → full database read/write access including user password hashes.

3. **C3 (HIGH)** — Diagnostics endpoint exposes the cookie signing key + weak `Math.random()` session IDs → forged session cookies → arbitrary user impersonation.

4. **C4 (HIGH)** — CORS `origin: true` with `credentials: true` + no CSRF tokens on POST endpoints → cross-origin state manipulation as any logged-in user.

### Top 3 Easiest Remediations
1. Remove/protect the diagnostics branch on the health endpoint (breaks C1 & C3)
2. Parameterize the search SQL query (breaks C2)
3. Move all secrets to environment variables (breaks remaining trust in C1/C3)
