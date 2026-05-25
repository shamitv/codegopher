

The chained vulnerability static audit is complete. Here's what was found:

## Audit Summary

| Metric | Result |
|---|---|
| **Chains Identified** | 5 |
| **Critical** | 1 (SQL Injection) |
| **High** | 3 (SQL Injection → Role Escalation, IDOR → Financial Fraud, CSRF → Balance Manipulation) |
| **Medium** | 1 (Exposed H2 Console) |
| **Files Reviewed** | 27 source/configuration/test files across controllers, services, config, models, repos, Dockerfile, and POM |

### Key Findings

1. **CRITICAL** — `UsageController.java` (line 27) builds SQL via string concatenation with unsanitized `@RequestParam` values, enabling arbitrary SQL execution on the H2 database.

2. **HIGH** — The SQL injection chains with the database-driven role system (`SecurityConfig.java` line 21-29) to allow role escalation, granting unauthorized ADMIN access to `AdminController`.

3. **HIGH** — `BillingController` has no ownership checks on invoice listing or payment endpoints, and `PaymentService` accepts any payment amount without comparing against the invoice total, enabling financial fraud.

4. **HIGH** — CSRF is globally disabled (`SecurityConfig.java` line 25), and the admin balance adjustment endpoint has no input validation or audit logging, enabling silent balance manipulation.

5. **MEDIUM** — The H2 console is publicly accessible (`permitAll()`) with X-Frame-Options disabled, providing a full SQL GUI to any unauthenticated visitor.

The full report with Mermaid attack graphs, file/line references, and remediation priorities has been written to:
`docs/security/CHAINED_VULNERABILITIES_REVIEW.md`
