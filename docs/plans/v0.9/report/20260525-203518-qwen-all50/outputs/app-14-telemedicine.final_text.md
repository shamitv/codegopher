

The chained vulnerability static audit is complete. The report has been written to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`. Here's a summary of findings:

## Audit Summary

**2 chained vulnerabilities detected:**

### Chain 1 — CRITICAL: JWT Secret Forgery → Full System Compromise
- **Source:** Hardcoded JWT secret `healthcare123` (src/index.ts:9)
- **Path:** Weak secret → any role can be forged in tokens → bypasses all auth middleware
- **Impact:** Complete system compromise — forge admin/doctor tokens, access all PHI
- **Remediation:** Move secret to environment variable with cryptographically random value

### Chain 2 — HIGH: IDOR on Single Appointment → PHI Leak
- **Source:** `/api/appointments/:id` endpoint (src/index.ts:168-183)
- **Path:** Accepts arbitrary appointment ID with no ownership verification against `req.user`
- **Impact:** Any authenticated user can read any other patient's full medical records including doctor notes
- **Remediation:** Add WHERE clause checking `patient_id` or `doctor_id` matches `req.user.userId`

**7 cross-cutting weaknesses** also identified: CORS misconfiguration, insecure cookie flags, verbose DB errors, hardcoded seed passwords, no rate limiting, and missing CSRF protection.

### P0 Remediation Priorities:
1. Rotate JWT secret to strong env variable
2. Add ownership check on `/api/appointments/:id`
