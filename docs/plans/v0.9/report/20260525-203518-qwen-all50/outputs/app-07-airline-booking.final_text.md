

The chained vulnerability audit report has been written to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`. Here's a summary of findings:

---

## Audit Results Summary

**4 chained vulnerabilities detected** across the airline booking system:

| # | Chain | Severity | Confidence |
|---|-------|----------|------------|
| 1 | **SQL Injection → Database Exfiltration / RCE** — Unparameterized queries in `FlightSearchDao.java` combined with exposed H2 web console | CRITICAL | HIGH |
| 2 | **CSRF-Disabled + Horizontal IDOR on Booking Cancel** — `csrf.disable()` + predictable PNRs + insufficient ownership checks allow unauthorized cancellation | HIGH | HIGH |
| 3 | **Stored XSS via Passenger Name → Boarding Pass Disclosure** — Unsanitized `firstName`/`lastName` at registration reflected unsafely in `/api/bookings/{pnr}/boarding-summary` API | HIGH | HIGH |
| 4 | **Session Fixation + CSRF + Predictable PNR → Account Takeover** — `sessionFixation().none()` + no CSRF + sequential PNRs enables full session hijack | MEDIUM | HIGH |

**7 additional cross-cutting weaknesses** were cataloged (H2 console exposure, verbose errors, missing rate limiting, unvalidated flight updates, hardcoded demo credentials, etc.).

The full report with Mermaid attack graphs, file/line references, evidence citations, and prioritized remediation guidance is in:

**`docs/security/CHAINED_VULNERABILITIES_REVIEW.md`**
