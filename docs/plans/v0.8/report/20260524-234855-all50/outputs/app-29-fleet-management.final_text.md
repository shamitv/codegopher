

## Chained Vulnerability Static Audit Complete

I've completed a comprehensive static-only review of this fleet management application and wrote the report to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`.

### Audit Summary

| Metric | Value |
|---|---|
| **Chains Found** | 4 |
| **Max Severity** | **CRITICAL** |
| **Cross-cutting Weaknesses** | 6 |

### Chains Identified

1. **SSRF via `/api/integrations/vehicle-data`** → Cloud metadata access & internal network pivot
   - `IntegrationController` passes user-controlled URL directly to `RestTemplate.getForObject()` with zero validation
   - Severity: **HIGH** | Confidence: High

2. **LDAP Filter Injection via `/api/drivers/lookup`** → Full driver database dump
   - `DriverService` uses string concatenation for LDAP queries (even the source comment admits this)
   - No authorization check on the endpoint
   - Severity: **HIGH** | Confidence: High

3. **Weak Seed Passwords + Basic Auth without TLS** → Credential compromise & role escalation
   - Seed passwords "dispatch123"/"fleet123" are trivially crackable
   - Basic Auth sends credentials in Base64 over cleartext (no TLS configured)
   - Severity: **MEDIUM** | Confidence: Medium

4. **Unauthenticated H2 Console + Default Credentials** → Full database compromise & potential RCE
   - `/h2-console/**` is `permitAll()` with `sa`/empty password
   - H2 supports arbitrary SQL execution
   - Severity: **CRITICAL** | Confidence: High

### Additional Findings

- **Log4j 2.14.1** (CVE-2021-44228 / Log4Shell) — not a chain but critical to fix immediately
- CSRF disabled, no input validation, verbose SQL logging, malformed `VehicleController.java`

The report includes prioritized remediation steps, Mermaid attack graphs, and recommended tests to add.
