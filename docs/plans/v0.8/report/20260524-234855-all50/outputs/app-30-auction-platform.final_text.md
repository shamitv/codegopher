

## Chained Vulnerability Static Audit Complete

I've completed the full four-phase audit of the auction platform codebase and written the report to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`.

### Findings Summary

| Chains Found | 3 total |
|---|---|
| **CRITICAL** | 1 — Unauthenticated transaction injection via webhook |
| **HIGH** | 2 — Bid race condition; Plaintext credential harvesting |
| **Cross-cutting weaknesses** | 5 (H2 console exposure, CSRF disabled, Basic auth, coarse authorization) |

### Key Chain Highlights

1. **Chain 1 — CRITICAL: Webhook Transaction Injection** — `/api/webhooks/payment` is `permitAll()` with zero signature validation. Any external actor can inject `COMPLETED` financial records with arbitrary amounts, buyer/seller IDs, and calculated platform fees. The code comment explicitly confirms: *"Direct processing ... without validating signatures or credentials"* (`WebhookController.java:25`).

2. **Chain 2 — HIGH: Bid Race Condition (TOCTOU)** — `BidService.placeBid()` reads the highest bid without `SELECT FOR UPDATE`, compares the new amount against a stale snapshot, then sleeps 50ms (widening the race window), and saves without re-validation. An attacker can send concurrent bids to bypass price checks (`BidService.java:26-38`).

3. **Chain 3 — HIGH: Plaintext Passwords** — `NoOpPasswordEncoder` is explicitly configured in `SecurityConfig.java:53-55`, making the `User.password` field truly plaintext. `DataInitializer.java:30-32` seeds three hardcoded accounts including `admin/adminpwd123`. Any database compromise yields all credentials outright.

### Additional Cross-Cutting Weaknesses
- H2 console exposed without authentication (`/h2-console/**` → `permitAll`)
- CSRF globally disabled
- Basic auth with no TLS enforcement
- Listing access by role instead of ownership
- Bid placement with no bidder-identity assertion

The full report includes Mermaid attack graphs, per-chain line references, confidence ratings, remediation priorities, and recommended test cases.
