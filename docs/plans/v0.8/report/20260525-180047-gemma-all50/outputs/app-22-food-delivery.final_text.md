

The chained vulnerability static audit is complete. Here's a summary:

## Audit Complete: `app-22-food-delivery`

**Files reviewed:** `app.py` (200 lines), `requirements.txt`, `Dockerfile`

### Chains Detected: 3

| Chain | Severity | Confidence | Summary |
|---|---|---|---|
| **1** | HIGH | High | Insecure cookies (`httponly=False`, `secure=False`) + permissive session validation → session hijack if any XSS vector exists |
| **2** | CRITICAL | High | Hardcoded `PAYMENT_SECRET` + simple string comparison + no ownership validation on webhook → anyone who reads the source can forge payment webhooks and mark any order as paid |
| **3** | MEDIUM (HIGH when chained) | Medium | No rate limiting + username enumeration + no CSRF → bulk account creation, brute-force, and forced order placement |

### 9 Cross-Cutting Weaknesses

Hardcoded secrets/test credentials, insecure cookies, no CSRF/rate-limiting, username enumeration, verbose errors, no TLS enforcement, no session expiry, no order idempotency, no audit logging.

### Top Remediation

1. **Move `PAYMENT_SECRET` to env vars + implement HMAC-SHA256** on webhook verification
2. **Set `httponly=True, secure=True, samesite='Lax'`** on session cookies
3. **Add rate limiting** to auth endpoints
4. **Add CSRF token validation** to all POST routes

Report written to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md` with full Mermaid attack graphs, code references, line numbers, evidence citations, and prioritized remediation steps.
