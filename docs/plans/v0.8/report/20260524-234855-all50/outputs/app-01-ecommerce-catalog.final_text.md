

The chained vulnerability static audit is complete. Here's a summary of what was found:

---

**Chained Vulnerability Audit Complete** ✅

**5 chains identified** across the ecommerce catalog codebase:

| # | Chain | Severity | Confidence |
|---|---|---|---|
| 1 | **SQL Injection → DB Exfiltration** — `GET /api/products?q=` uses f-string interpolation with debug query feedback | **CRITICAL** | HIGH |
| 2 | **Plaintext Passwords → Account Takeover** — Hardcoded plaintext credentials in both `app.py` and `index.html` | **CRITICAL** | HIGH |
| 3 | **No CSRF → Admin Privilege Escalation** — State-changing endpoints lack CSRF tokens; admin creds are public | **CRITICAL** | HIGH |
| 4 | **Stored XSS → Session Hijacking** — Admin product creation accepts unsanitized input; rendered via `innerHTML` in frontend | **CRITICAL** | HIGH |
| 5 | **IDOR → Cross-User Data Exfiltration** — `GET /api/orders/<id>` has no ownership check | **HIGH** | HIGH |

**8 cross-cutting weaknesses** were also catalogued (hardcoded session secret, verbose errors, debug mode, no rate limiting, missing security headers, client-side admin checks, etc.).

The report has been written to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md` with full Mermaid attack graphs, file/line references, and prioritized remediation steps.
