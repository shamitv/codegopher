

# Chained Vulnerability Static Audit Complete ✅

The comprehensive report has been written to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`.

## Findings Summary

**5 chained vulnerabilities** identified across the recruitment ATS platform:

| Chain | Severity | Confidence | Key Finding |
|-------|----------|------------|-------------|
| **1** | HIGH | HIGH | Zip Slip via unsanitized ZIP entry paths → arbitrary file write |
| **2** | HIGH | HIGH | MD5(user_id) API keys + wildcard CORS → any account impersonation |
| **3** | HIGH | HIGH | Plaintext seed passwords in source → immediate full account takeover |
| **4** | MEDIUM | MEDIUM | No SameSite/CSRF protection + CORS wildcard → cross-site request forgery |
| **5** | LOW-MEDIUM | HIGH | Unindexed full-table API key lookup → performance + timing attacks |

**6 cross-cutting weaknesses** also catalogued (bcrypt rounds, in-memory sessions, verbose errors, missing input validation, in-memory SQLite, exposed API key endpoint).

### Critical Fixes Required (P0):
1. **Add path-prefix validation** on ZIP extraction (`path.resolve(targetPath).startsWith(path.resolve(uploadDir))`)
2. **Replace MD5-based API keys** with `crypto.randomBytes(32)`
3. **Remove plaintext passwords** from source code — use env vars or a secrets manager
