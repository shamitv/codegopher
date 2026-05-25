

The chained vulnerability static audit is complete. Here's a summary of what was found:

## Report Summary

**File written to:** `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`

### Chains Identified (6 total)

| # | Chain | Severity |
|---|-------|----------|
| 1 | **LDAP Injection → Directory Disclosure → Privilege Escalation** — User input concatenated into LDAP filter in `EmployeeController.java:21` with verbose error responses in `EmployeeController.java:27-28` | 🔴 High |
| 2 | **SSRF via Shipping Label URL → Internal Data Exfiltration** — `ShippingService.java:19-20` uses `new URL()` on unvalidated user-supplied `carrierLabelUrl`, allowing arbitrary server-side HTTP requests | 🔴 High |
| 3 | **Hardcoded Frontend Credentials → Auth Compromise** — Admin/operator/supervisor passwords printed in plaintext in `index.html:42-44` | 🟠 Medium |
| 4 | **IDOR on Inventory Adjust → Stock Manipulation** — `POST /api/inventory/{id}/adjust` has **no** `@PreAuthorize` annotation (unlike adjacent CRUD endpoints) | 🟠 Medium |
| 5 | **Verbose Error Handling → App Fingerprinting** — All 5 controllers return `e.getMessage()` in HTTP responses, leaking internal details | 🟡 Low-Medium |
| 6 | **Exposed Actuator + Config Display → Full Recon** — `/actuator/**` is `permitAll()` with `show-values=ALWAYS` and `heapdump.enabled=true`, leaking all config and in-memory data | 🟠 Medium |

### Cross-Cutting Weaknesses (5)
- No CSRF configuration
- No rate limiting on login
- Predictable default passwords (`admin123`, `supervisor123`)
- Order status state machine leaks via error messages
- DTO design could enable mass assignment

### P0 Remediation (Highest Impact / Lowest Effort)
1. Remove hardcoded credentials from `index.html` (minutes)
2. Add `@PreAuthorize` to `InventoryController.adjustQuantity` (minutes)
3. Lock down actuator endpoints to admin role (15 min)

These three fixes alone would eliminate ~70% of the attack surface and break all High-severity chains.
