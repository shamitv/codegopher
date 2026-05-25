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

### Subtle Ssrf Pivot To Auth Session

- Chain ID: `chain-02`
- Impact: data_modification
- Scenario: Attacker combines a low-visibility entry point with stored or derived application state, then pivots to a higher-impact sink that is reachable only after following the cross-file flow.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A10 | critical | `src/main/java/com/warehouse/service/ShippingService.java` | `generateLabel` | Shipping label URL fetched server-side via HttpURLConnection with no scheme, host, or port validation — allows access to cloud metadata, internal services, and local files |
| 2 | A03 | high | `src/main/java/com/warehouse/service/EmployeeLdapService.java` | `searchEmployees` | LDAP filter constructed via string concatenation with user-supplied search term, enabling LDAP injection to enumerate all employees or extract hidden attributes |
| 3 | A05 | high | `src/main/resources/application.properties` | `application` | Spring Boot Actuator endpoints (env, heapdump, beans, mappings) exposed publicly without authentication via management.endpoints.web.exposure.include=* |
