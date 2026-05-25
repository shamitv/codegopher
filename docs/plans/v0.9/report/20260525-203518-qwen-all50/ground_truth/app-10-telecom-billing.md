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

### Subtle State Confusion Pivot To Injection

- Chain ID: `chain-02`
- Impact: data_modification
- Scenario: Attacker combines a low-visibility entry point with stored or derived application state, then pivots to a higher-impact sink that is reachable only after following the cross-file flow.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A09 | low | `src/main/java/com/telecom/billing/controller/AdminController.java` | `adjustBalance` | Admin balance adjustment endpoint lacks audit logging, allowing undetectable database modification |
| 2 | A04 | medium | `src/main/java/com/telecom/billing/service/PaymentService.java` | `processPayment` | No rate limiting or idempotency check on the payment processing service |
| 3 | A03 | high | `src/main/java/com/telecom/billing/controller/UsageController.java` | `getUsageByDateRange` | Usage search SQL query constructed using string concatenation with user-supplied date values |
