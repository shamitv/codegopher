

## Audit Complete

The chained vulnerability static audit has been completed and the report written to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`.

### Summary of Findings

**3 Chained Vulnerabilities Identified:**

| Chain | Severity | Description |
|-------|----------|-------------|
| **CHAIN-01** | **High** | Mass assignment on `/api/auth/profile` lets any user set their own role (e.g., WORKER → QA_MANAGER), granting full authenticated access |
| **CHAIN-02** | **Medium** | `POST /api/defects/{id}/resolve` has no role check — any user can close any defect without QA Manager approval |
| **CHAIN-03** | **High** | CSRF disabled + mass assignment + no audit trail enables silent privilege escalation and inspection data manipulation |

**5 Cross-Cutting Weaknesses (no full chain):**
- **WC-01:** Default credentials seeded (`worker/worker123`, etc.)
- **WC-02:** H2 console exposed publicly with `permitAll()`
- **WC-03:** No rate limiting on authentication
- **WC-04:** Dockerfile skips all tests (`-DskipTests`)
- **WC-05:** Inconsistent authorization (`@PreAuthorize` only on `ProductController`, missing on `InspectionController` and `DefectController`)

### Key Attack Surface

- **Entry points:** 4 REST controllers (Auth, Defect, Inspection, Product)
- **Authentication:** HTTP Basic (no rate limiting, no lockout)
- **Authorization:** Partial — only `ProductController` has `@PreAuthorize`; profile and defect endpoints are wide open
- **Data store:** In-memory H2 with console exposed publicly

### Top Priority Remediations

1. Add authorization checks to `AuthController.updateProfile()` and `DefectController.resolveDefect()`
2. Remove `permitAll()` for `/h2-console/**` or disable the console entirely
3. Re-enable CSRF protection in `SecurityConfig`
4. Add audit logging for all data mutations
5. Remove default credentials from `DataInitializer`
