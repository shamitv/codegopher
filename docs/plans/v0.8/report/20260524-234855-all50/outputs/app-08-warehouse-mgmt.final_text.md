

The chained vulnerability static audit is complete. Here's a summary of findings:

## Audit Complete — 4 Chains Identified

### Chains Found

| # | Chain | Severity | Confidence |
|---|---|---|---|
| **1** | LDAP Injection → Verbose Errors → Employee PII Harvesting | **Medium** | High |
| **2** | Exposed Actuator → Env/Heapdump Disclosure → Credential Exposure | **Medium** | High |
| **3** | Unvalidated Carrier URL → SSRF → Internal Network Access | **High** | High |
| **4** | Inconsistent Authorization → Inventory Manipulation + Data Exfiltration | **Medium** | High |

### Critical Findings

- **Chain 3 (HIGH)**: `ShippingService` blindly trusts `request.getCarrierLabelUrl()` and passes it to `new URL()` + `HttpURLConnection` with no scheme validation, hostname allowlist, or size limits — enabling SSRF to internal services and cloud metadata endpoints.

- **Chain 2 (MEDIUM)**: `/actuator/**` is `permitAll()` in SecurityConfig, and `application.properties` sets `env.show-values=ALWAYS` and `heapdump.enabled=true` — exposing all configuration including DB credentials and enabling heap dump extraction.

- **Chain 1 (MEDIUM)**: LDAP search filter directly concatenates user input (`"(&(objectClass=inetOrgPerson)(|(cn=*" + searchTerm + "*)(uid=*" + searchTerm + "*)))"`) with no escaping, and error responses leak internal DN paths.

- **Chain 4 (MEDIUM)**: The `/api/inventory/adjust` endpoint has no `@PreAuthorize`, allowing any authenticated OPERATOR to arbitrarily change inventory quantities. All read endpoints (inventory, orders, dashboard) lack role-based access control.

- **7 cross-cutting weaknesses** identified including CSRF gaps, weak test credentials (`admin123`), empty DB password, SQL logging in production, no CSP/CORS, and unbounded `readAllBytes()` in SSRF.

Full report written to **`docs/security/CHAINED_VULNERABILITIES_REVIEW.md`** with Mermaid attack graphs, file/line references, and prioritized remediation actions (P0–P3).
