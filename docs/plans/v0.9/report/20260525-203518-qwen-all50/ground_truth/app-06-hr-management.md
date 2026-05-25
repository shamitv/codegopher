# Ground Truth - app-06-hr-management

- App key: `app-06-hr-management`
- Source path: `<secure-code-hunt>\apps\java\app-06-hr-management`
- Language/framework: java / spring-boot

## Expected Chained Attacks

### Credential Hash Harvest → Offline Crack → Payroll + SSN Exfiltration

- Chain ID: `chain-01`
- Impact: db_exfiltration
- Scenario: A low-privilege employee iterates the audit endpoint to collect password hashes for all employees, cracks the hashes offline using a wordlist attack, re-authenticates as an HR Admin, then dumps all payroll records and decrypts SSNs using the hardcoded XOR key.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A01 | medium | `src/main/java/com/hr/controller/EmployeeController.java` | `getEmployeeAudit` | GET /api/employees/{id}/audit exposes passwordHash for any employee to any authenticated user — no role or ownership check |
| 2 | A02 | low | `src/main/java/com/hr/config/DataInitializer.java` | `seed` | Seed data uses short common passwords; hashes crackable offline with a standard wordlist, providing access to higher-privilege accounts |
| 3 | A01 | high | `src/main/java/com/hr/controller/PayrollController.java` | `getPayroll` | Payroll endpoint returns salary and encrypted SSN for any employee to any authenticated session without role or ownership validation |

### Subtle Crypto Pivot To Idor

- Chain ID: `chain-02`
- Impact: db_exfiltration
- Scenario: Attacker combines a low-visibility entry point with stored or derived application state, then pivots to a higher-impact sink that is reachable only after following the cross-file flow.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A02 | high | `src/main/java/com/hr/model/Employee.java` | `setRawSsn` | SSN encryption uses reversible XOR cipher with hard-coded key 0xDEADBEEF |
| 2 | A08 | critical | `src/main/java/com/hr/service/EmployeeImportService.java` | `importEmployees` | Bulk employee import uses ObjectInputStream.readObject() on untrusted upload without class filtering |
| 3 | A01 | high | `src/main/java/com/hr/controller/PayrollController.java` | `getPayroll` | Payroll endpoint returns salary data for any employee to any authenticated user without role or ownership check |
