

The chained vulnerability static audit is complete. Here's a summary of what was found:

## Audit Summary

**6 attack chains** were identified across the airline booking codebase, ranging from **CRITICAL** to **MEDIUM** severity:

| Chain | Severity | Description |
|-------|----------|-------------|
| **1** | 🔴 **CRITICAL** | SQL injection in flight search via string concatenation in `FlightSearchDao.java` — enables full database read/write |
| **2** | 🟠 **HIGH** | Predictable sequential PNRs + missing ownership check on `getBoardingSummary()` endpoint — enables mass data enumeration |
| **3** | 🟠 **HIGH** | CSRF explicitly disabled (`csrf.disable()`) — enables unauthorized booking/cancellation from malicious pages |
| **4** | 🟡 **MEDIUM** | Stored XSS vector via registration fields reflected in JSON API response without escaping |
| **5** | 🟡 **MEDIUM** | Race condition in seat booking — two concurrent requests can book the same seat due to TOCTOU without locking |
| **6** | 🟠 **HIGH** | H2 console exposed publicly at `/h2-console` with `web-allow-others=true` — unauthenticated full database access |

**5 additional cross-cutting weaknesses** were also documented (verbose errors, no rate limiting, demo credentials on login page, session fixation disabled, missing security headers).

The report includes full code references (file paths, line numbers), Mermaid attack graphs for each chain, impact assessments, confidence ratings, and prioritized remediation steps.
