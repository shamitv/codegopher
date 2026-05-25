# Ground Truth - app-08-warehouse-mgmt

- App key: `app-08-warehouse-mgmt`
- Source path: `<secure-code-hunt>\apps\java\app-08-warehouse-mgmt`
- Language/framework: java / spring-boot

## Expected Chained Attacks

### LDAP Injection → Directory Structure Disclosure → Inventory Tampering

- Chain ID: `chain-01`
- Impact: data_modification
- Scenario: Attacker injects a malformed LDAP filter that triggers an exception; the verbose error response reveals internal DN paths and account naming conventions. The attacker authenticates with a discovered worker account and calls the unprotected inventory adjustment endpoint to zero out stock counts.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A03 | medium | `src/main/java/com/warehouse/service/EmployeeLdapService.java` | `searchEmployees` | LDAP filter built by direct string concatenation of user input in searchEmployees(), enabling injection to enumerate arbitrary directory entries |
| 2 | A05 | low | `src/main/java/com/warehouse/controller/EmployeeController.java` | `search` | LDAP exceptions including internal DN paths are returned verbatim in the HTTP 500 error body, revealing directory structure to the attacker |
| 3 | A01 | high | `src/main/java/com/warehouse/controller/InventoryController.java` | `adjustQuantity` | POST /api/inventory/{id}/adjust requires only authentication (no role check), allowing any worker account to modify stock quantities for any item |
