

The chained vulnerability static audit is complete. Here's what was found:

## Summary

**5 chained vulnerabilities** were identified across the event ticketing codebase:

| # | Chain | Severity | Confidence |
|---|-------|----------|------------|
| 1 | SQL Injection in `/api/events/search` → Full DB exfiltration via UNION | HIGH | HIGH |
| 2 | Race condition in `/api/tickets/book` (no transaction/locking) → Ticket overbooking & hoarding | HIGH | HIGH |
| 3 | Weak 6-digit `Math.random()` session IDs → Account takeover via bruteforce | HIGH | HIGH |
| 4 | Wildcard CORS (`origin: true`) + SQLi → Cross-origin data theft | MEDIUM-HIGH | MEDIUM |
| 5 | Hardcoded plaintext admin credentials + weak sessions → Admin account takeover | MEDIUM-HIGH | HIGH |

**4 cross-cutting weaknesses** were also cataloged (verbose errors, no CSRF, no rate limiting, hardcoded creds).

All 5 chains are **statically provable** from cited source code — no live probes were needed. The report has been written to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md` with Mermaid attack graphs, detailed chain breakdowns, code references with line numbers, and prioritized remediation steps.
