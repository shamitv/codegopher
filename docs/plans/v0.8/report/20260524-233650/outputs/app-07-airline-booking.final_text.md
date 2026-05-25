

The chained vulnerability static audit is complete. The report has been written to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`.

## Summary

| Metric | Value |
|--------|-------|
| **Total Chains Found** | 6 |
| **Critical** | 1 (SQL Injection → DB Exfiltration) |
| **High** | 4 (CSRF/Session Fixation, Priv Escalation, Error Leakage, H2 Console) |
| **Medium** | 1 (PNR Enumeration/Privacy Leak) |

### Priority Remediation Order

1. **Chain 1 — SQL Injection**: Parameterize `FlightSearchDao.java:20-22` — fixes the critical chain
2. **Chain 5 — H2 Console**: Disable `spring.h2.console.enabled=false` in `application.properties`
3. **Chain 2 — CSRF/Session Fixation**: Re-enable CSRF, session fixation migration, and frame options in `SecurityConfig.java`
4. **Chain 3 — Demo Credentials**: Remove hardcoded staff credentials from `home.html` and gate `DataInitializer` behind a dev profile
5. **Chain 4 — Verbose Errors**: Add `@ControllerAdvice` global error handler to stop leaking `e.getMessage()` to clients
6. **Chain 6 — PNR Enumeration**: Switch to UUIDs and add ownership checks to `/boarding-summary`

All 10 cross-cutting weaknesses were cataloged (race conditions, missing CSP, no rate limiting, deprecated XSS header, etc.), and 9 tests were recommended for the test suite.
