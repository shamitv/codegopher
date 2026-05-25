# Ground Truth - app-06-hr-management

- App key: `app-06-hr-management`
- Source path: `D:\work\secure-code-hunt\apps\java\app-06-hr-management`
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
