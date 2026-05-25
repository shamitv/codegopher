

The chained vulnerability static audit is complete. Here's what I found:

## Audit Summary

I reviewed **30 source files** across controllers, services, config, models, DTOs, repositories, frontend assets, and configuration. Three chained vulnerabilities were identified:

| Chain | Severity | What It Does |
|---|---|---|
| **C1 — SSRF via Carrier Label URL** | **HIGH** | `ShippingService` passes user-controlled `carrierLabelUrl` directly to `new URL()` with no validation, allowlist, or scheme restriction. Any authenticated user (OPERATOR+) can make the server fetch arbitrary URLs, enabling internal network scanning and cloud metadata access. |
| **C2 — Missing Auth on Inventory Adjust** | **MEDIUM** | `POST /api/inventory/{id}/adjust` has **no `@PreAuthorize` annotation**, while other inventory endpoints (POST, PUT, DELETE) require SUPERVISOR/ADMIN. Any authenticated user can arbitrarily inflate or deflate any item's stock quantity. |
| **C3 — LDAP Injection** | **MEDIUM** | `EmployeeLdapService` concatenates the `q` parameter directly into an LDAP filter string: `"(&(objectClass=inetOrgPerson)(|(cn=*"+searchTerm+"*)(uid=*"+searchTerm+"*)))"`. No escaping or parameterized search. Combined with the endpoint having no `@PreAuthorize`, the directory is fully enumerable. |

## Key Cross-Cutting Weaknesses (9 found)

- **Exposed actuator endpoints** — `permitAll()` on `/actuator/**` with `env.show-values=ALWAYS` and `heapdump.enabled=true`
- **No CSRF protection** — Spring Security configuration has no `.csrf()` call
- **Verbose error messages** across all controllers — `e.getMessage()` leaked to clients
- **Hardcoded credentials** in both seed data and SPA source (`index.html` shows `admin123`)
- **Unprotected read endpoints** — inventory, orders, shipping labels, employee search all lack `@PreAuthorize`
- **No CORS configuration**, **no security headers**, **SQL logging in production**, **H2 in-memory DB**

## Report Written To

`docs/security/CHAINED_VULNERABILITIES_REVIEW.md`

The report includes full Mermaid attack graphs, per-chain file/line citations, confidence ratings, and a prioritized remediation table.
