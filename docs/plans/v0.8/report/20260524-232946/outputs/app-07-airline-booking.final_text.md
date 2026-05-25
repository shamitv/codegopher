

The chained vulnerability static audit is complete. Here's a summary of what was found:

## Audit Summary

**4 chained vulnerabilities** identified across the Apex Airlines Booking System:

| Chain | Severity | Confidence | Description |
|---|---|---|---|
| **Chain 1** | 🔴 High | High | SQL Injection in `FlightSearchDao.java` via string concatenation in raw SQL, reachable unauthenticated at `/api/flights/search` |
| **Chain 2** | 🔴 High | High | XSS via unescaped passenger names in `/api/bookings/{pnr}/boarding-summary` JSON response, enabled by client-side `innerHTML` usage |
| **Chain 3** | 🟡 Medium | High | Sequential PNR enumeration + IDOR — `getBoardingSummary()` has no email ownership check, exposing any authenticated user's booking data |
| **Chain 4** | 🟡 Medium | High | CSRF protection globally disabled (`csrf.disable()`) — state-changing endpoints (booking creation, cancellation, check-in) are CSRF-vulnerable |

Additionally documented **10 cross-cutting weaknesses** including exposed H2 console, session fixation protection disabled, hardcoded demo credentials, booking race conditions, and verbose error messages.

The full report is written to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md` with Mermaid attack graphs, per-hop evidence with file paths and symbols, and a prioritized remediation matrix.
