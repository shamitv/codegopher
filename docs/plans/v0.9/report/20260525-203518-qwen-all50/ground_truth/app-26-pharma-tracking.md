# Ground Truth - app-26-pharma-tracking

- App key: `app-26-pharma-tracking`
- Source path: `D:\work\secure-code-hunt\apps\java\app-26-pharma-tracking`
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

### Subtle Deserialization Pivot To Idor

- Chain ID: `chain-02`
- Impact: data_modification
- Scenario: Attacker combines a low-visibility entry point with stored or derived application state, then pivots to a higher-impact sink that is reachable only after following the cross-file flow.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A08 | critical | `src/main/java/com/pharma/tracking/service/BatchImportService.java` | `importBatch` | Insecure Java deserialization on batch import endpoint allows execution of arbitrary code via malicious payloads |
| 2 | A02 | medium | `src/main/java/com/pharma/tracking/service/CustodyService.java` | `generateCustodySignature` | Weak MD5 hashing algorithm without a secret key is used to sign custody transfers, allowing forged signatures |
| 3 | A01 | medium | `src/main/java/com/pharma/tracking/controller/BatchController.java` | `getBatchDetails` | IDOR on batch lookup allows any authenticated user to view details of any batch without checks |
