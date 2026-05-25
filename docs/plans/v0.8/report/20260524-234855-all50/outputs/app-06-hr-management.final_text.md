

The chained vulnerability static audit is complete. Here's a summary of findings:

---

## Audit Complete — Report Written

**Report location:** `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`

### 4 Attack Chains Identified

| # | Chain | Severity | Confidence |
|---|---|---|---|
| 1 | **Java Deserialization RCE** via `/api/employees/import` — `.ser` file → `ObjectInputStream.readObject()` → RCE | **CRITICAL** | High |
| 2 | **Credential Hash Exposure → Password Cracking → Privilege Escalation** via `/api/employees/{id}/audit` — no auth → hash exfiltration → offline cracking → admin access | **HIGH** | High |
| 3 | **Role Manipulation → Full Admin Takeover** via `/api/employees` POST/PUT — `role` field accepted from payload with no allowlist validation | **HIGH** | High |
| 4 | **Employee ID Enumeration + Payroll Data Leak** — `/api/payroll/{id}` and `/api/employees?q=` have no authorization/scoping | **MEDIUM** | High |

### 7 Cross-Cutting Weaknesses (WC-1 through WC-7)

Including exposed H2 console, hardcoded DB password, XOR-based "SSN encryption," disabled CSRF, no login rate limiting, plaintext demo credentials on login page, and developer comments acknowledging unfixed security gaps.

### P0 Priorities

1. **Replace `EmployeeImportService` deserialization** with a safe format (CSV/JSON) — breaks Chain 1
2. **Remove `passwordHash` from audit endpoint response** — breaks Chain 2 exposure hop
3. **Add role allowlist validation** in `createEmployee`/`updateEmployee` — breaks Chain 3
