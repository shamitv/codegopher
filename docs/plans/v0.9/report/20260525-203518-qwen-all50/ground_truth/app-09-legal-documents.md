# Ground Truth - app-09-legal-documents

- App key: `app-09-legal-documents`
- Source path: `<secure-code-hunt>\apps\java\app-09-legal-documents`
- Language/framework: java / spring-boot

## Expected Chained Attacks

### Log4Shell Trigger → Path Traversal → Legal Document Exfiltration

- Chain ID: `chain-01`
- Impact: lateral_movement
- Scenario: Attacker submits a case title containing a JNDI expression; Log4j 2.14.1 evaluates it, triggering Log4Shell RCE. The executed payload then calls the path-traversal file endpoint to read signing keys and legal document content from the server filesystem.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A06 | medium | `src/main/java/com/legal/controller/CaseController.java` | `createCase` | Case title logged verbatim via Log4j 2.14.1 logger.info(); a JNDI expression in the title triggers Log4Shell remote code execution |
| 2 | A01 | high | `src/main/java/com/legal/controller/DocumentController.java` | `serveDocumentFile` | GET /api/documents/file?name= concatenates the parameter to a base path without normalization, allowing path traversal to read arbitrary server files |

### Subtle State Confusion Pivot To Idor

- Chain ID: `chain-02`
- Impact: lateral_movement
- Scenario: Attacker combines a low-visibility entry point with stored or derived application state, then pivots to a higher-impact sink that is reachable only after following the cross-file flow.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A06 | critical | `pom.xml` | `pom` | Application imports and uses log4j-core:2.14.1 as logging dependency, making it vulnerable to Log4Shell (CVE-2021-44228) when logging user-controlled request headers |
| 2 | A02 | high | `src/main/java/com/legal/model/Document.java` | `Document` | Highly sensitive corporate legal contracts, lawsuit briefs, and depositions are stored directly in plaintext database columns without any encryption at rest |
| 3 | A01 | high | `src/main/java/com/legal/controller/DocumentController.java` | `downloadDocument` | Document download endpoint performs no validation to verify if the currently authenticated client has ownership or case access authorization to retrieve the requested document, leading to horizontal IDOR bypass |
