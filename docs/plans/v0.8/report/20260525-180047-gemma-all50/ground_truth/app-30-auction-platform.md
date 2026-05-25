# Ground Truth - app-30-auction-platform

- App key: `app-30-auction-platform`
- Source path: `<secure-code-hunt>\apps\java\app-30-auction-platform`
- Language/framework: java / spring-boot

## Expected Chained Attacks

### Plaintext Password Dump → Forged Webhook → Transaction Fraud

- Chain ID: `chain-01`
- Impact: data_modification
- Scenario: Attacker exfiltrates plaintext passwords via database access or a separate SQL injection, logs in as a seller to list items, and forges unsigned payment webhooks directly to the server to fake payment completion without transfer of actual money.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A07 | low | `src/main/java/com/auction/platform/model/User.java` | `n/a` | Plaintext passwords stored directly in the DB allows easy credential theft. |
| 2 | A08 | medium | `src/main/java/com/auction/platform/controller/WebhookController.java` | `handlePaymentWebhook` | Webhook endpoint accepts payment notifications without signature verification. |
