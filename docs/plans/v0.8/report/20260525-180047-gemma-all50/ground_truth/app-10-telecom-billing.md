# Ground Truth - app-10-telecom-billing

- App key: `app-10-telecom-billing`
- Source path: `<secure-code-hunt>\apps\java\app-10-telecom-billing`
- Language/framework: java / spring-boot

## Expected Chained Attacks

### SQL Injection → Payment Fraud → No Audit Trail

- Chain ID: `chain-01`
- Impact: data_modification
- Scenario: Attacker exploits SQL injection in usage search to leak invoice details, submits multiple forged or replayed payment confirmations via the non-idempotent payment endpoint, and utilizes unlogged admin balance adjustments to complete fraud.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A03 | medium | `src/main/java/com/telecom/billing/controller/UsageController.java` | `getUsageByDateRange` | SQL injection in usage lookup allows exfiltrating details of other customers' invoices. |
| 2 | A04 | medium | `src/main/java/com/telecom/billing/service/PaymentService.java` | `processPayment` | Payment endpoint lacks concurrency / replay / rate-limiting controls, allowing payment fraud. |
| 3 | A09 | low | `src/main/java/com/telecom/billing/controller/AdminController.java` | `adjustBalance` | Admin balance adjustments are not audit logged. |
