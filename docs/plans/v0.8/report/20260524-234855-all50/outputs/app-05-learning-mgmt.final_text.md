

The chained vulnerability static audit is complete. Here's a summary:

---

## Audit Complete ✅

**Report written to:** `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`

### Key Findings

| Metric | Value |
|--------|-------|
| **Chains Detected** | 3 |
| **Maximum Severity** | **CRITICAL** |

### Chain Summary

| # | Severity | Description |
|---|----------|-------------|
| **Chain 1** | CRITICAL | `/api/debug/config` exposes the Flask secret key (no auth) → attacker forges admin sessions → gains access to `/api/courses/import` → `pickle.loads()` on untrusted base64 data → **RCE** |
| **Chain 2** | MEDIUM | `/api/submissions/<id>` lacks ownership checks → authenticated students can enumerate and read all other students' quiz answers and scores |
| **Chain 3** | MEDIUM-HIGH | Hardcoded plaintext passwords (lines 36-39) + no password hashing → trivial credential exposure and admin impersonation |

### Top 3 Immediate Fixes (P0)

1. **Delete `/api/debug/config`** — exposes secret key, environment variables, and Python version
2. **Replace `pickle.loads()` with JSON** — untrusted deserialization is RCE
3. **Hash passwords** using `werkzeug.security` and remove all hardcoded credentials

### Additional Notes

- 5 cross-cutting weaknesses identified (no CSRF, verbose errors, debug mode, input validation)
- The codebase is a single-file Flask app with SQLite, making every link in each chain statically provable with **High confidence**
- Docker runs with default root user, exposes port 8085 without TLS indication
