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

### Subtle Ssrf Pivot To State Confusion

- Chain ID: `chain-02`
- Impact: data_modification
- Scenario: Attacker combines a low-visibility entry point with stored or derived application state, then pivots to a higher-impact sink that is reachable only after following the cross-file flow.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A08 | medium | `src/main/java/com/auction/platform/controller/WebhookController.java` | `handlePaymentWebhook` | Webhook listener accepts arbitrary payloads without verifying payment signatures, allowing forged payment notifications |
| 2 | A07 | high | `src/main/java/com/auction/platform/model/User.java` | `n/a` | User passwords are saved in plaintext directly in the database without any hashing |
| 3 | A04 | medium | `src/main/java/com/auction/platform/service/BidService.java` | `placeBid` | Bidding workflow suffers from race conditions allowing multiple concurrent lower bids to win or execute due to lack of db locks |
