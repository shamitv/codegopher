

## Audit Complete

The chained vulnerability static audit has been completed and the report written to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`.

### Key Findings Summary

| Chain | Severity | Confidence | Description |
|---|---|---|---|
| **Chain 1** | **Critical** | High | **Log4Shell RCE** — `pom.xml` pins `log4j-core` to vulnerable version `2.14.1`. `CaseController.java:44` interpolates user-supplied `dto.getTitle()` directly into a `logger.info()` call. A crafted `${jndi:ldap://...}` title triggers remote code execution. |
| **Chain 2** | **High** | High | **Path Traversal → Arbitrary File Read** — `DocumentController.java:81-82` concatenates `fileName` query param directly to a base path without `Path.normalize()` or a `startsWith()` guard, allowing `../` traversal to read any file the JVM can access. |
| **Chain 3** | **Medium** | High | **Pre-seeded Weak Credentials** — `DataInitializer.java` creates admin/attorney/client accounts with simple passwords (`admin123`, `attorney123`, `client123`) at startup. Combined with role disclosure in `UserController`, this enables unauthorized data access. |

### Cross-Cutting Weaknesses (6 found)
- CSRF disabled in `SecurityConfig.java`
- No rate limiting on `/login`
- H2 DB with no password
- Debug security logging enabled in production
- No CORS configuration
- Unrestricted file content upload with no size/type limits

### Most Urgent Remediation
1. **Upgrade Log4j** to ≥ 2.17.1 in `pom.xml` (breaks Chain 1)
2. **Fix path traversal** using `Path.normalize()` + prefix validation (breaks Chain 2)
