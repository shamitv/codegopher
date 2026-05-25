

The chained vulnerability static audit is complete. Here's a summary:

## Findings Overview

| Metric | Value |
|---|---|
| **Complete attack chains** | **4** |
| **Max severity** | **CRITICAL** |
| **Highest confidence** | **HIGH** |

## 4 Chains Identified

### Chain 1: SQL Injection → Full Database Control (HIGH / HIGH confidence)
`MeterController.java:43-48` — `meterSerial` and `dateRange` HTTP parameters are directly concatenated into a native SQL string and executed via `entityManager.createNativeQuery()`. No parameterization or input sanitization.

### Chain 2: SSRF via Smart Meter Integration (HIGH / HIGH confidence)
`IntegrationController.java:22` — A user-supplied `meterEndpointUrl` parameter is forwarded directly to `RestTemplate.getForObject()` with no URL validation, host filtering, or scheme checking. Can reach cloud metadata endpoints and internal services.

### Chain 3: H2 Console Unauthenticated Access (CRITICAL / HIGH confidence)
`SecurityConfig.java:28` — `.requestMatchers("/h2-console/**").permitAll()` provides an unauthenticated path to an interactive SQL console on the application database.

### Chain 4: Broken Authorization on Invoice Endpoint (HIGH / HIGH confidence)
`BillingController.java:20-24` — `GET /api/invoices/{id}` returns any invoice to any authenticated user with no ownership or role-based check. Enables cross-customer financial data exfiltration.

## 8 Cross-Cutting Weaknesses

CSRF disabled, weak seed passwords (`"cust123"`, `"billing123"`), verbose error messages, no rate limiting, no CORS config, over-permissive TECHNICIAN role access, hardcoded passwords in source, and a suboptimal `RestTemplate` instantiation.

The full report has been written to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`.
