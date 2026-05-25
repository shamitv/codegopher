

The chained vulnerability static audit is complete. Here's a summary of what was found:

## Audit Summary

**3 Chained Vulnerabilities** detected, **1 HIGH** maximum severity:

| Chain | Path | Severity |
|-------|------|----------|
| **1** | SQL Injection in `/api/restaurants/search?q=` → arbitrary SQL → full database exfiltration | **HIGH** |
| **2** | SQL Injection → password hash extraction → offline cracking of weak seed passwords → account takeover → unbounded review editing (no ownership check) | **HIGH** |
| **3** | Non-cryptographic `Math.random()` session IDs → predictable/hijackable sessions → CORS wildcard + no CSRF → authenticated impersonation (gated by role check) | **MEDIUM** |

**6 Cross-Cutting Weaknesses** identified including plaintext passwords in source, CORS misconfiguration, verbose error messages, no session expiration, no CSRF protection, and username enumeration via registration errors.

The **easiest remediation link** to break the most damaging chains is using parameterized queries for the SQL search endpoint — this single fix breaks both Chain 1 and the first hop of Chain 2. The full report with Mermaid attack graphs, code references, line numbers, and prioritized remediation steps has been written to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`.
