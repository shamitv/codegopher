# Ground Truth - app-26-pharma-tracking

- App key: `app-26-pharma-tracking`
- Source path: `<secure-code-hunt>\apps\java\app-26-pharma-tracking`
- Language/framework: java / spring-boot

## Expected Chained Attacks

### IDOR Batch Enumeration → Forged Custody Signature → Supply Chain Tampering

- Chain ID: `chain-01`
- Impact: data_modification
- Scenario: Attacker logs in, uses IDOR to search all batch shipment details, and generates a fake MD5 custody signature to divert or inject custom chain-of-custody transfer entries.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A01 | medium | `src/main/java/com/pharma/tracking/controller/BatchController.java` | `getBatchDetails` | IDOR batch endpoint leaks details of batches not belonging to the current user's organization. |
| 2 | A02 | medium | `src/main/java/com/pharma/tracking/service/CustodyService.java` | `generateCustodySignature` | Weak custody signature algorithm allows generating valid transfer signatures off-platform. |
