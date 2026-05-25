

The report has been successfully written to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`. Here is a summary of the findings:

---

## Audit Results: Library Book Reservation System

### 3 Chained Vulnerabilities Detected

| # | Severity | Chain Summary | Confidence |
|---|---|---|---|
| **Chain 1** | **CRITICAL** | SQL injection in `/api/books/search` (`src/index.js:144–145`) — user-controlled `req.query.q` is interpolated directly into SQL, then executed via `db.all()`. Enables full database exfiltration including all user password hashes. | **High** |
| **Chain 2** | **HIGH** | Weak session IDs (`Math.random()` at line 112) + CORS `origin: true` with `credentials: true` (line 10) + no CSRF protection → predictable session IDs allows session hijacking and account takeover. | **Medium** |
| **Chain 3** | **MEDIUM** | Verbose error messages exposing DB details (line 148) + weak MD5 password hashing (lines 50, 94, 104) + no rate limiting on login (line 104) → password hash extraction + offline cracking → account takeover. | **Medium** |

### 4 Cross-Cutting Weaknesses
- **CW-1:** Hardcoded plaintext passwords in source (`src/index.js:44–47`)
- **CW-2:** No role-based access control checks
- **CW-3:** Session cookie missing `Secure` flag
- **CW-4:** Console.log port disclosure on startup

### Top Remediation Priorities
1. **P0:** Parameterize the SQL query in `/api/books/search` (breaks Chain 1)
2. **P0:** Replace MD5 with bcrypt/scrypt/argon2 (breaks Chain 3)
3. **P1:** Replace `Math.random()` with `crypto.randomBytes(32)` (breaks Chain 2)
4. **P2:** Restrict CORS origins and add CSRF tokens
