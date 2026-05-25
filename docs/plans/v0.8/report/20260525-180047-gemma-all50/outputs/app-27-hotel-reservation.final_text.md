

The chained vulnerability static audit is complete. Here's a summary of what was found:

---

## Audit Results Summary

### 5 Chained Vulnerabilities Found

| # | Chain | Severity | Confidence |
|---|---|---|---|
| 1 | **Unauthenticated Database Dump** — H2 console + exposed DB credentials → full SQL access | **CRITICAL** | High |
| 2 | **Public Admin Credentials → Admin Takeover** — `/api/admin/debug` exposes admin/adminpwd123 unauthenticated | **CRITICAL** | High |
| 3 | **JPQL Injection in Room Search** — unsanitized `type`/`status` params concatenated into JPQL | **HIGH** | High |
| 4 | **Mass Reservation Data Exposure** — no role check on `GET /api/reservations`, any user sees all bookings | **Medium-High** | High |
| 5 | **Admin Credentials + IDOR → PII Exfiltration** — admin role bypasses IDOR check, leaking all guest data | **Medium-High** | High |

### 3 Cross-Cutting Weaknesses
- CSRF disabled (352)
- Verbose error messages (209)  
- H2 frame options disabled (284)

### Areas Not Reviewed
- Dependency CVE scanning, TLS config, rate limiting, audit logging, deployment infrastructure

The report has been written to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`.
