

I've completed the Chained Vulnerability Static Audit and written the report to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`. Here's a summary of findings:

## Key Findings

**3 chained vulnerabilities identified:**

1. **Chain 1 (HIGH)** — **IDOR in `get_patient_records`**: Any authenticated user can access any patient's PHI by providing an arbitrary `patient_id`. The endpoint checks authentication but never verifies the caller owns the requested record.

2. **Chain 2 (HIGH)** — **MD5 Hashing + Info Disclosure + No Rate Limiting → Account Takeover → PHI Exfiltration**: 
   - Different error messages enable username enumeration
   - Unlimited login attempts with no rate limiting
   - Unsalted MD5 is trivially crackable offline
   - 4 hardcoded seed accounts with simple passwords (`alice/alice123`, `admin/admin123`, etc.)
   - Followed by IDOR (Chain 1) for full data exfiltration

3. **Chain 3 (MEDIUM)** — **Insecure Session Cookies → Session Hijacking → PHI Harvesting**: `SESSION_COOKIE_SECURE = False`, `@csrf_exempt` on login and appointment endpoints, and `ALLOWED_HOSTS = ['*']` make session theft and abuse relatively easy.

**5 cross-cutting weaknesses** also documented, including a hardcoded `SECRET_KEY`, missing CSRF protections, verbose search results leaking PII, database seeding side-effects in the views module, and unscoped STAFF queries.

All chains include specific file paths, line references, Mermaid attack graphs, confidence ratings, and prioritized remediation steps.
