# Hygiene - app-09-legal-documents

- Passed: yes
- Removed evaluator files: 3
- Sanitized source hints: 6
- Residual source hints: 0

## Removed Evaluator Files

- `.vulns`
- `README.md`
- `scenarios.md`

## Sanitized Source Hints

- `src/main/java/com/legal/config/SecurityConfig.java:87` stripped-inline-comment: return new BCryptPasswordEncoder(); // Secure hashing decoy
- `src/main/java/com/legal/controller/DocumentController.java:54` removed-line: // Retrieves the document directly solely by document id parameter, enabling IDOR.
- `src/main/java/com/legal/controller/DocumentController.java:69` removed-line: // Vulnerable: no canonicalization — ../../ traversal can escape basePath
- `src/main/java/com/legal/model/Document.java:1` removed-line: A02: Storing highly sensitive legal documents in cleartext
- `src/main/resources/static/index.html:298` removed-visible-hint-line: <label class="form-label" for="addDocContent">Plaintext File Content (A02 target)</label>
- `src/main/resources/static/js/app.js:307` removed-line: // Send requests to doc download endpoint (contains the vulnerable Log4j call)

## Residual Source Hints

- None
