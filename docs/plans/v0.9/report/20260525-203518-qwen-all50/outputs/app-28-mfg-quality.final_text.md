

# Chained Vulnerability Static Audit — Complete

I have completed the full static-only chained vulnerability review of the Manufacturing Quality Control System and written the report to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`.

## Findings Summary

| # | Chain | Severity | Confidence |
|---|---|---|---|
| **1** | Mass Assignment → Privilege Escalation → Full RBAC Bypass | **HIGH** | HIGH |
| **2** | Mass Assignment → Defect Resolution Without QA Approval | **HIGH** | HIGH |
| **3** | Unauthenticated H2 Console → Full DB Exfiltration | **HIGH** | HIGH |
| **4** | Role Escalation → Silent Inspection Tampering (No Audit Trail) | **MEDIUM** | HIGH |

## Key Findings

### 🔴 Critical: Mass Assignment (`AuthController.java:30-37`)
The `PUT /api/auth/profile` endpoint deserializes the full `User` request body and **unconditionally** calls `user.setRole(profileUpdate.getRole())` without any role validation or authorization guard. Any authenticated user (even `worker` with password `worker123`) can escalate to `QA_MANAGER` or `COMPLIANCE`.

### 🔴 Critical: H2 Console Exposed Without Auth (`SecurityConfig.java:32`)
`/h2-console/**` is set to `.permitAll()`, the DB password is empty, and `spring.h2.console.enabled=true`. An unauthenticated attacker gets full SQL access to the database — including user credentials and all quality control data.

### 🟡 Medium: Silent Inspection Tampering (`InspectionService.java:24`)
Inspection results can be modified by any authenticated user with **no audit trail** — a PASS/FAIL result can be overwritten silently, undermining the entire quality process.

## Cross-Cutting Weaknesses (6)
- Hardcoded seed credentials in `DataInitializer`
- CSRF disabled
- No input validation on inspection results
- Verbose SQL logging in production config
- X-Frame-Options disabled (clickjacking risk)
- In-memory DB with no persistence guarantee

## Top 3 Remediations
1. **Add `@PreAuthorize` guards** to all mutating endpoints, especially `/api/auth/profile` and `/api/defects/{id}/resolve`
2. **Remove mass assignment** — use a dedicated DTO that excludes the `role` field from profile updates
3. **Disable H2 console in production** — set `spring.h2.console.enabled=false` and restrict `/h2-console/**` access
