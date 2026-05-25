

The chained vulnerability static audit is complete. Here's a summary of findings:

## Findings at a Glance

### 🔴 2 Chained Vulnerabilities Found

| # | Severity | Title | Confidence |
|---|---|---|---|
| 1 | **CRITICAL** | RCE via unrestricted Java deserialization of user-uploaded batch import file | HIGH |
| 2 | **MEDIUM** | Supply-chain tampering via missing authorization on batch import + custody transfers | HIGH |

### Key Evidence

**Chain 1 (RCE):** `BatchController` accepts a file upload → `BatchImportService` passes it directly to `ObjectInputStream.readObject()` → arbitrary JVM code execution. The file path at `BatchImportService.java:20` has zero filtering on what gets deserialized.

**Chain 2 (Data Poisoning):** Any authenticated user (regardless of role) can import arbitrary `Batch` objects and forge custody transfer records. No `@PreAuthorize` guards exist on `importBatch` or `transferBatch`, and the `fromEntity`/`toEntity` parameters are used as-is without org-ownership validation.

### 8 Cross-Cutting Weaknesses

- H2 console exposed without authentication
- MD5 used for custody integrity signatures
- No organization/tenant scoping despite `User.orgName` existing
- Hardcoded seed passwords in source
- No input validation on `@RequestParam` fields
- Verbose error messages exposed
- Frame Options disabled
- CSRF disabled (mitigated by Basic Auth, but worth documenting)

### Report Written To

`docs/security/CHAINED_VULNERABILITIES_REVIEW.md` — includes Mermaid attack graphs, line-level code references, impact assessments, and a prioritized remediation roadmap.
