

The chained vulnerability static audit is complete. The report has been written to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`.

---

## Audit Results Summary

### 4 Chained Vulnerabilities Detected

| # | Severity | Chain Description | Key Files |
|---|----------|-------------------|-----------|
| **1** | **CRITICAL** | SQL Injection via Meter Reading Search → Full Database Compromise | `MeterController.java:24-31` |
| **2** | **CRITICAL** | SSRF via Smart Meter Integration → Internal Network Reconnaissance | `IntegrationController.java:14-18` |
| **3** | **CRITICAL** | SSRF + H2 Console Exposure → Full Database Compromise | `IntegrationController.java` + `SecurityConfig.java:28` + `application.properties:8` |
| **4** | **HIGH** | IDOR on Invoice API → Customer PII & Billing Data Leakage | `BillingController.java:16-21` |

### 6 Cross-Cutting Weaknesses (Not Full Chains)
- Hardcoded seed credentials (`DataInitializer.java:39-40`)
- CSRF disabled globally (`SecurityConfig.java:27`)
- H2 frame options disabled (`SecurityConfig.java:26`)
- Verbose error messages exposing entity existence (`BillingController.java:19`)
- No input validation on `Invoice.totalAmount` (`Invoice.java`)
- `RestTemplate` not thread-safe (`IntegrationController.java:14`)

### Key Findings

- **Chain 3 is the most dangerous** — it requires two independently exploitable weaknesses (SSRF + H2 console exposure with `permitAll()` + `web-allow-others=true`), but both are statically provable from source. An attacker with valid credentials could load the H2 web console via SSRF and execute arbitrary SQL.

- **Chain 1 is trivially exploitable** — the meter reading search endpoint concatenates user input directly into native SQL with zero parameterization or sanitization.

- **Chain 4 reveals an authorization inconsistency** — `CustomerController` properly checks ownership before returning data, but `BillingController` does not, creating an IDOR gap that allows any authenticated user to enumerate all invoices.

### Remediation Priority
1. **P0** — Parameterize SQL in `MeterController`; validate URLs in `IntegrationController`; disable H2 console in production
2. **P1** — Add authorization check to `BillingController.getInvoice()`
3. **P2+** — Move seed credentials to env vars, enable CSRF, add input validation, configure RestTemplate timeouts

The report includes detailed Mermaid attack graphs, line references for every link in each chain, impact assessments, and recommended tests to add.
