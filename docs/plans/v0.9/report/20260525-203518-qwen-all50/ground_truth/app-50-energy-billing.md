# Ground Truth - app-50-energy-billing

- App key: `app-50-energy-billing`
- Source path: `D:\work\secure-code-hunt\apps\java\app-50-energy-billing`
- Language/framework: java / spring-boot

## Expected Chained Attacks

### SSRF → H2 Console Access → Database Exfiltration

- Chain ID: `chain-01`
- Impact: db_exfiltration
- Scenario: Attacker triggers SSRF via the smart meter endpoint to target the unauthenticated H2 database console listening on localhost, bypassing network blocks to execute arbitrary SQL and dump all customer data.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A10 | medium | `src/main/java/com/energy/billing/controller/IntegrationController.java` | `fetchSmartMeterData` | SSRF allows sending requests to internal endpoints. |
| 2 | A05 | medium | `src/main/java/com/energy/billing/config/SecurityConfig.java` | `filterChain` | H2 database console is enabled without security check. |

### Subtle Ssrf Pivot To Idor

- Chain ID: `chain-02`
- Impact: db_exfiltration
- Scenario: Attacker combines a low-visibility entry point with stored or derived application state, then pivots to a higher-impact sink that is reachable only after following the cross-file flow.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A10 | medium | `src/main/java/com/energy/billing/controller/IntegrationController.java` | `fetchSmartMeterData` | Smart meter endpoint fetches user-supplied URLs without validation, enabling server-side request forgery |
| 2 | A05 | medium | `src/main/java/com/energy/billing/config/SecurityConfig.java` | `filterChain` | H2 web console is enabled and permitted without authentication, offering direct database access |
| 3 | A03 | high | `src/main/java/com/energy/billing/controller/MeterController.java` | `searchReadings` | Meter reading native query constructed by string concatenation with user parameters allows SQL injection |
| 4 | A01 | medium | `src/main/java/com/energy/billing/controller/BillingController.java` | `getInvoice` | IDOR on invoice retrieval allows customer accounts to read details of other customers' invoices without checks |
