

## Audit Complete

The chained vulnerability static audit has been completed and the report written to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`.

### Key Findings

**4 Chained Vulnerabilities Detected:**

| # | Chain | Severity |
|---|---|---|
| 1 | **Role Escalation via Mass Assignment** — A WORKER can PUT `{"role": "QA_MANAGER"}` to `/api/auth/profile` and get admin privileges | HIGH |
| 2 | **Critical Defect Resolution Bypass** — Any authenticated user (including WORKER) can close CRITICAL defects at `POST /api/defects/{id}/resolve` with no role check | HIGH |
| 3 | **H2 Console Data Exfiltration** — Unauthenticated access to `/h2-console` provides full SQL shell on the application database | HIGH |
| 4 | **Inspection Result Tampering Without Audit Trail** — Any authenticated user can silently change inspection results (FAIL→PASS) with no logging | MEDIUM |

**6 Cross-Cutting Weaknesses:** CSRF disabled globally, default debug credentials seeded, verbose SQL logging, IDOR on all ID-based endpoints, no global exception handler, Dockerfile runs as root.

**P0 Remediations (highest priority):**
1. Remove role field from profile update endpoint
2. Disable H2 console or gate it behind authentication
3. Add `@PreAuthorize("hasRole('QA_MANAGER')")` to the defect resolve endpoint
