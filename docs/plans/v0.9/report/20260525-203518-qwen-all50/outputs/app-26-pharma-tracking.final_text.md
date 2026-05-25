

The chained vulnerability audit is complete. Here's a summary of what was found:

## Audit Results

**5 chains detected** across the pharmaceutical drug tracking application:

| Chain | Severity | Description |
|---|---|---|
| 1 | 🔴 Critical | **RCE via insecure deserialization** — `BatchImportService` accepts raw `ObjectInputStream` from uploaded files with no whitelist or type checking |
| 2 | 🔴 Critical | **Unauthenticated H2 console** — `/h2-console/**` is `permitAll()` with no database password, granting full SQL access |
| 3 | 🟠 High | **CSRF-enabled custody transfer** — CSRF is globally disabled and transfers have no role checks, enabling forged custody records |
| 4 | 🔴 Critical | **Weak seeded passwords → account takeover** — seeded passwords like `pharma123`, `inspect123` are trivially crackable, granting INSPECTOR role for forging inspections |
| 5 | 🟡 Medium | **Unscoped data access** — authenticated users can read any batch, drug, or inspection regardless of organization |

### 7 Cross-Cutting Weaknesses
- CSRF disabled globally
- MD5 used for tamper-evident custody signatures (cryptographically broken)
- No rate limiting on authentication
- Verbose error messages in exception handling
- JPA SQL logging enabled in properties
- Dead `ReferenceGuards` utility (never invoked)
- No TLS configuration

### Easiest Fix
Replace the `ObjectInputStream` deserialization in `BatchImportService` with safe JSON/CSV parsing — this alone eliminates the highest-impact chain (full RCE).
