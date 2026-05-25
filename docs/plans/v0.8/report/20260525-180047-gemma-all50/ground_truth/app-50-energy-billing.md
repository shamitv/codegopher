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
