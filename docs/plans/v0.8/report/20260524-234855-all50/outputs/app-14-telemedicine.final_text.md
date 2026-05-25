

## Chained Vulnerability Static Audit Complete

The report has been written to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`. Here's a summary:

### 3 Chains Detected — Maximum Severity: HIGH

**Chain 1: Hardcoded JWT Secret → Token Forgery → Full PHI Exfiltration**
- Root cause: `const JWT_SECRET = 'healthcare123'` (line 13)
- Attacker can forge arbitrary JWT tokens with any userId/role
- Broken at multiple links: misconfigured JWT secret, insecure cookie settings (`httpOnly: false`, `secure: false`), and missing row-level authorization on both appointment endpoints
- Impact: Any authenticated user can read all appointment records including doctor notes (HIPAA-violating PHI disclosure)

**Chain 2: Permissive CORS + Insecure Cookie + CSRF → Cross-Domain Session Hijacking**
- Root cause: `cors({ origin: true, credentials: true })` (line 17) + missing `SameSite` cookie attribute
- Any malicious origin can make authenticated cross-origin requests and read responses
- Impact: Cross-domain session hijacking — attacker reads PHI from any logged-in user's session

**Chain 3: Hardcoded Seed Credentials + Public Registration + IDOR → Automated Account Takeover**
- Root cause: Plaintext passwords in source (`john_pass_123`, `admin_pass_2026`, etc.) following predictable patterns
- Public registration has no rate limiting, password policy, or email verification
- Impact: Automated brute-force or pattern-guessing attacks succeed trivially

### 9 Cross-Cutting Weaknesses
Including verbose error messages, no rate limiting, no HTTPS enforcement, no audit logging, and in-memory database.

### P0 Remediation (easiest links to break)
1. Move `JWT_SECRET` to `process.env` with 32-byte minimum
2. Add row-level authorization (`WHERE patient_id = ?` or `doctor_id = ?`) to all appointment endpoints
3. Remove all hardcoded seed credentials from source
4. Replace `origin: true` with an explicit allowlist
