

The static-only chained vulnerability audit is complete. Here's a summary of what was found and written to the report:

---

## Audit Complete — 5 Chains Found

| Chain | Severity | Key Weaknesses Combined |
|---|---|---|
| **1. Unauthenticated Transaction Fraud** | High | `permitAll` on webhooks + no signature validation + transaction saved as COMPLETED without wallet deduction |
| **2. Account Takeover via Plaintext Passwords** | Critical | `NoOpPasswordEncoder` + hardcoded plaintext credentials in `DataInitializer` + user model stores raw passwords |
| **3. Bid Manipulation via IDOR + Race Condition** | High | Client-controlled `bidderId` + no `@Transactional`/`@Lock` + `Thread.sleep(50)` widening TOCTOU window |
| **4. SQL Injection / DB Access via H2 Console** | Critical | `spring.h2.console.enabled=true` + `permitAll` on `/h2-console/**` + empty `sa` password |
| **5. CSRF-Authenticated Financial Action** | Medium | `.csrf(AbstractHttpConfigurer::disable)` + unauthenticated POSTs accepted at `/api/bids` |

Additionally, **11 cross-cutting weaknesses** were cataloged (no input validation, missing rate limiting, disabled X-Frame-Options, no HTTPS enforcement, verbose SQL logging, etc.) and **6 areas not reviewed** (Docker runtime, dependency CVEs, production profiles, CORS, network exposure).

The full report has been written to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md` with Mermaid attack graphs, per-chain breakdowns with file/line/symbol references, and a remediation priority matrix.
