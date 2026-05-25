

The chained vulnerability static audit is complete. The report has been written to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`.

### Key Findings

| # | Chain | Severity | Confidence |
|---|-------|----------|------------|
| 1 | **Log4Shell RCE** via `POST /api/cases` (case title logged unsanitized into Log4j 2.14.1) | Critical | High |
| 2 | **Path Traversal** via `GET /api/documents/file?fileName=` (no `normalize()` or `startsWith()` guard) | High | High |
| 3 | **Log4Shell via User-Agent header** in `GET /api/documents/{id}` (alternative entry point) | High | High |

### Cross-Cutting Weaknesses
- CSRF disabled in `SecurityConfig.java`
- H2 database console potentially exposed with empty password
- Verbose error messages leaking internal details
- Sensitive seed data hardcoded in `DataInitializer.java`

### Root Cause
The **Log4Shell (CVE-2021-44228)** vulnerability is the linchpin: `pom.xml` explicitly pins Log4j at version **2.14.1** (override of the Spring Boot managed version), and both `CaseController` and `DocumentController` concatenate user-controlled input into `logger.info()` calls without parameterized logging. This single misconfiguration enables RCE and serves as the first hop into the path traversal chain.

### Easiest Fix
Remove the `<log4j2.version>2.14.1</log4j2.version>` override from `pom.xml` so Spring Boot 3.2.5 manages a patched version, and switch all logging to parameterized syntax (`logger.info("msg: {}", value)`).
