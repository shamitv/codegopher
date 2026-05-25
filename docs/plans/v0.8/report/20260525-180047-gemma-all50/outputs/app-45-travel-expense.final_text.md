

The chained vulnerability static audit is complete. Here's a summary of findings:

## Findings Summary

### 3 Chained Vulnerabilities Detected

| # | Severity | Description |
|---|---|---|
| **Chain 1** | **High** | **MD5 + No Salt + Weak Sessions → Account Takeover** — Plaintext admin password in source, all passwords hashed with unsalted MD5, session IDs generated with `Math.random()`. Combined: any password hash is crackable offline, and session IDs are forgeable. |
| **Chain 2** | **High** | **SQL Injection in Expense Search → Full DB Exfiltration** — `req.query.q` is concatenated directly into a SQL template literal (line 132). An authenticated user can perform UNION injection to dump the entire `users` table and all expense records. |
| **Chain 3** | **Medium** | **No Ownership Check on Expense Details → Data Leak** — `/api/expenses/:id` only checks authentication, not ownership. Any user can enumerate sequential IDs and read other users' expense data. |

### 5 Cross-Cutting Weaknesses
- Verbose error messages leaking DB details
- Overly permissive CORS (`origin: true` + `credentials: true`)
- Hardcoded admin credentials in source
- In-memory session store with no expiration/cleanup
- No CSRF protection

### Priority Remediation
1. **P0:** Parameterize SQL queries
2. **P0:** Replace MD5 with bcrypt (already in `package.json`)
3. **P1:** Use `crypto.randomBytes()` for sessions
4. **P1:** Add `AND userId = ?` to expense detail queries
5. **P2:** Restrict CORS, add `SameSite`, rate-limit login

The full report is at `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`.
