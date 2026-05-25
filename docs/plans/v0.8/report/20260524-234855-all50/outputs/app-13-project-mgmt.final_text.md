

## Summary

The chained vulnerability static audit is now complete. The report has been written to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`.

### Key Findings

| Metric | Value |
|---|---|
| Chained vulnerabilities | **4** |
| Max severity | **High** |
| Cross-cutting weaknesses | **4** |

### Chains Identified

1. **Stored XSS (Task Descriptions)** — `app.js:137` innerHTML renders unsanitized `description` → High / High confidence
2. **Stored XSS (Comments)** — `src/index.ts:24-25` stores raw content → High / High confidence
3. **IDOR Cross-Tenant Data Access** — `src/index.ts:10` `find(b => b.id === boardId)` lacks `orgId` scoping → Medium-High / High confidence
4. **CSRF + Unlogged Permission Change** — `src/index.ts:3-16` PUT endpoint with no CSRF token and commented-out audit log → High / Medium confidence

### Areas Not Reviewed
- External auth service (`/api/auth/*` routes)
- Database layer (`db` object implementation)
- Runtime CORS/session cookie configuration
- Production environment and TLS

### Recommendation
The two **easiest remediation links** to break are:
1. Replace `innerHTML` with `textContent` in `app.js:137-141` (breaks both XSS chains)
2. Add `orgId` scoping to board queries in `src/index.ts:10` (breaks the IDOR chain)
