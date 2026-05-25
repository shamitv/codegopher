

The chained vulnerability static audit is complete. The report has been written to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`.

### Audit Results Summary

**5 attack chains** were identified across this Spring Boot airline booking application:

| Chain | Severity | Summary |
|-------|----------|---------|
| **CHAIN-01** | HIGH | Unauthenticated SQL injection via `/api/flights/search` (raw string concatenation in `FlightSearchDao.java`) |
| **CHAIN-02** | HIGH | H2 Web Console exposed to internet + SQL injection — dual vectors for full database takeover |
| **CHAIN-03** | MEDIUM | CSRF protection disabled + unprotected state-changing APIs (`POST /api/bookings`, `PUT /api/bookings/{pnr}/cancel`) |
| **CHAIN-04** | MEDIUM | Session fixation protection disabled (`fixation.none()`) — known session ID can survive login |
| **CHAIN-05** | MEDIUM | IDOR on `/api/bookings/{pnr}/boarding-summary` — no ownership check lets any user view any booking; verbose error messages enable PNR enumeration |

**6 cross-cutting weaknesses** were cataloged (race condition on seat booking, verbose errors, missing DTO validation, predictable PNRs, etc.) that could compound with other issues.

The two highest-priority fixes are **parameterizing the SQL query** in `FlightSearchDao.java` and **disabling/restricting the H2 console** — both directly break CHAIN-01 and CHAIN-02.
