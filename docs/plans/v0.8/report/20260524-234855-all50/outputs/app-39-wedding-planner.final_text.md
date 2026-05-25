

The chained vulnerability static audit is complete. Here's a summary of what was found:

## Audit Results for Wedding Planning Platform

**4 chained vulnerabilities identified** across the single-source-file codebase (`src/index.js`):

| Chain | Severity | Key Flaws | Impact |
|---|---|---|---|
| **Chain 1** | **HIGH** | MD5 hashing + no rate limiting → brute force → IDOR on events/guests | Full PII exfiltration (guest emails, names, RSVPs) |
| **Chain 2** | **HIGH** | Hardcoded admin password (`plannerSecure2026!`) in source | Direct admin account takeover |
| **Chain 3** | **MEDIUM** | `Math.random()` session IDs + no CSRF + permissive CORS | Session hijacking + cross-origin guest manipulation |
| **Chain 4** | **MEDIUM** | Open registration + CORS + no rate limiting | Mass account creation + username enumeration |

**10 additional cross-cutting weaknesses** were cataloged (no `SameSite` cookie attribute, no HTTP security headers, no TLS, no email validation, etc.).

The report has been written to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md` with full code references, Mermaid attack graphs, and prioritized remediation steps for each chain.
