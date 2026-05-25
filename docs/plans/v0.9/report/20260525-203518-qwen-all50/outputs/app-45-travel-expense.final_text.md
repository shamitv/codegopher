

The chained vulnerability static audit is complete. Here's a summary of what was found:

## Key Findings

**3 chains detected** with a maximum severity of **HIGH**:

| Chain | Severity | Description |
|---|---|---|
| **Chain 1** | HIGH | SQL injection in `/api/expenses/search` — user-controlled `req.query.q` is interpolated directly into a SQL template literal (line 143), enabling UNION-based credential theft. Verbose error messages (`err.message`, line 145) aid injection crafting. |
| **Chain 2** | MEDIUM | Weak hashing (MD5 without salt, lines 46 & 100) combined with hardcoded seed passwords (lines 42-46). The admin password `accountantSecure2026!` is plaintext in source, enabling direct admin login. Note: `bcryptjs` is a dependency but never used. |
| **Chain 3** | MEDIUM | Insecure session IDs (`Math.random()`, line 110) + missing CSRF protection across all POST endpoints enables session hijacking and unauthorized expense creation. Permissive CORS (`origin: true`, line 11) lowers the barrier further. |

**6 cross-cutting weaknesses** were identified, including an **IDOR vulnerability** on `/api/expenses/:id` (no ownership check — any authenticated user can read any expense).

The full report with Mermaid attack graphs, line-level evidence, confidence ratings, and prioritized remediation steps has been written to:

**`docs/security/CHAINED_VULNERABILITIES_REVIEW.md`**
