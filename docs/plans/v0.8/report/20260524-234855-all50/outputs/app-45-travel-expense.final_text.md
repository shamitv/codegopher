

## Audit Complete — Report Written to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`

### Executive Summary

This single-file Express.js travel expense application has **5 chained vulnerabilities** (3 HIGH, 2 MEDIUM) and **11 cross-cutting weaknesses**. Here are the highlights:

| Chain | Description | Severity |
|---|---|---|
| **1** | **SQL Injection** in `GET /api/expenses/search` via unsanitized `req.query.q` in a template literal → full database exfiltration | **HIGH** |
| **2** | **Weak session IDs** (`Math.random()`) + **no CSRF protection** + **permissive CORS** (`origin: true`) → session hijacking / CSRF account actions | **HIGH** |
| **3** | **Hardcoded plaintext admin credentials** + **MD5 hashing** + unused `bcryptjs` → full credential compromise | **HIGH** |
| **4** | **SQL Injection** + **error message disclosure** (`details: err.message`) → schema enumeration & data extraction | **MEDIUM** |
| **5** | **Missing authorization** on `GET /api/expenses/:id` — no ownership check — any authenticated user can read any expense | **MEDIUM** |

### Top 3 Immediate Fixes

1. **Replace the SQL-injected search query** (`src/index.js:143`) with parameterized queries using `?` placeholders
2. **Switch to `bcryptjs`** for all password hashing — it's already a dependency, just unused
3. **Add `userId` check** to the expense-by-ID endpoint (`src/index.js:133-134`) so users can only read their own records

The full report includes Mermaid attack graphs for each chain, precise line references, remediation code snippets, unknowns, and a prioritized testing backlog.
