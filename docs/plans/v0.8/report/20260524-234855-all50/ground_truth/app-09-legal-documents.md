# Ground Truth - app-09-legal-documents

- App key: `app-09-legal-documents`
- Source path: `D:\work\secure-code-hunt\apps\java\app-09-legal-documents`
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
