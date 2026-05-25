

The chained vulnerability audit is complete. Here's a summary of what was found:

**5 chained vulnerabilities identified** (max severity: **High**):

1. **SQL Injection → Full DB Exfiltration** (High): The `/api/events/search` endpoint concatenates user input directly into a SQL query via template literal interpolation, with verbose error responses that leak the query back to the attacker.

2. **Weak Session Tokens → Account Takeover** (High): Session IDs are 6-digit numbers from `Math.random()`, providing only ~900K possible values — trivially brute-forceable.

3. **TOCTOU Race Condition → Ticket Hoarding** (High): The booking flow checks availability then updates stock in two separate statements without transactions, allowing race conditions that lead to overbooking or ticket hoarding.

4. **Permissive CORS + No CSRF → Session Hijack** (Medium): `cors({ origin: true, credentials: true })` mirrors the `Origin` header back, and no CSRF protection exists on authenticated endpoints.

5. **Hardcoded Admin Password + No RBAC → Admin Takeover** (High): The admin plaintext password (`admin_tickets_2026`) is visible in source code, and there is no role-based access control on any endpoint.

The full report has been written to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`.
