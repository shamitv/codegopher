

The chained vulnerability static audit is complete. Here's a summary of what was found:

## Audit Results Summary

**5 chained vulnerabilities** were identified across the telecom billing codebase:

| # | Chain | Severity | Confidence | Key Elements |
|---|---|---|---|---|
| 1 | **SQL Injection → Database Exfiltration** | Critical | High | `UsageController.java:30-35` — raw SQL string concatenation via native query |
| 2 | **SQL Injection → Privilege Escalation → Balance Manipulation** | High | High | Chains off #1, exploits trust-based role in `SecurityConfig`, reaches `AdminController.adjustBalance()` with zero auditing |
| 3 | **Cross-Customer Data Breach + Unauthorized Payments** | High | Medium | `BillingController` lacks Principal-based ownership checks on `/api/billing/invoices` and `/api/billing/pay` |
| 4 | **Payment Amount Not Validated → Revenue Loss** | Medium | High | `PaymentService.processPayment()` sets invoice to PAID regardless of submitted `amount` vs. `totalAmount` |
| 5 | **H2 Console Exposed → Database Shell Access** | Medium | High | `/h2-console/**` is `permitAll()` in `SecurityConfig` |

**Additional cross-cutting weaknesses** include CSRF being disabled, customer PII leaked in full entity responses, no rate limiting on login, and Spring Security debug logging enabled.

**Top remediation priority:** Fix the SQL injection in `UsageController.java` (line 32-33) — this single change breaks both Chain 1 and Chain 2. The report has been written to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`.
