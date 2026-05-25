

The chained vulnerability static audit is complete. The report has been written to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`.

## Audit Summary

**4 confirmed chained vulnerabilities** were identified across 4 phases of analysis:

| Chain | Severity | Key Finding |
|---|---|---|
| **Chain 1** | HIGH | Unprotected `/api/employees/{id}/audit` endpoint leaks BCrypt password hashes to any authenticated user, enabling offline cracking of admin credentials |
| **Chain 2** | CRITICAL | Java deserialization via `ObjectInputStream.readObject()` on user-uploaded `.ser` files — remote code execution with HR_ADMIN auth |
| **Chain 3** | MEDIUM | IDOR on `/api/payroll/{employeeId}` — any authenticated user can query salary data for any employee via predictable IDs |
| **Chain 4** | MEDIUM | Leave approval endpoint has no department scoping — any MANAGER can approve/reject any employee's leave request |

**7 cross-cutting weaknesses** were also cataloged:
- CSRF disabled (`SecurityConfig.java`)
- Plaintext demo credentials on login page
- Weak XOR "encryption" for SSNs with hardcoded key (`0xDEADBEEF`)
- H2 console exposed without authentication
- Stored XSS via unsanitized employee names in `innerHTML`
- No file upload size limits
- No database migrations

The report includes Mermaid attack graphs, detailed source-code references with line numbers, confidence ratings, and prioritized remediation guidance (P0–P3).
