

The chained vulnerability audit is complete. Here's a summary of the findings:

---

## Audit Results

**2 complete chains detected**, plus 5 cross-cutting weaknesses:

| Chain | Severity | Description |
|---|---|---|
| **Chain 1** | **CRITICAL** | Unrestricted Java deserialization at `POST /api/batches/import` (BatchImportService.java:20) allows any authenticated user to inject arbitrary Batch entities into the database |
| **Chain 2** | **HIGH** | Open `/h2-console/**` access (no auth) + weak seed passwords + IDOR-unprotected endpoints → SQL access → credential cracking → full API enumeration |
| **Chain 3** | **MEDIUM** | `POST /api/custody/transfer` has no authorization — any authenticated user can forge custody chain records with arbitrary from/to entities |

### Cross-Cutting Weaknesses

1. **CSRF protection disabled** (`SecurityConfig.java:33`)
2. **Weak hardcoded passwords** in seed data (`DataInitializer.java:37-40`)
3. **MD5 for custody signatures** (`CustodyService.java:22`) — cryptographically broken
4. **User-supplied `inspectorId`** in inspection creation — not validated against caller
5. **Verbose error messages** exposing internal exception chains

### Easiest Fix (P0)

Replace the `ObjectInputStream` deserialization in `BatchImportService` with a JSON-based parser — this single change eliminates the most severe chain entirely.

The full report has been written to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`.
