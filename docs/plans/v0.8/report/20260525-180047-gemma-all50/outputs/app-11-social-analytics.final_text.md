

# Chained Vulnerability Static Audit Complete

The report has been written to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`.

## Findings Summary

**5 attack chains** were identified across this Social Analytics Dashboard:

| # | Severity | Chain Summary |
|---|----------|---------------|
| 1 | **CRITICAL** | SSRF → Cloud Metadata Credential Exfiltration via unvalidated `axios.get()` with deliberately removed 500-char response cap |
| 2 | **HIGH** | Stored XSS → Session/Token Theft via unsanitized widget title injected through `innerHTML` |
| 3 | **CRITICAL** | Hardcoded Credentials → Auth Bypass via `alice/alice123` and `bob/bob123` plaintext in served HTML |
| 4 | **HIGH** | SSRF → Internal Service Reconnaissance → Header Leakage via `/api/debug/headers` exposing all `req.headers` |
| 5 | **MEDIUM** | Verbose Errors + SSRF → Information Disclosure via `error.message` returned verbatim to client |

## Key Cross-Cutting Weaknesses
- No Content Security Policy
- No CSRF protection
- Debug endpoint in production
- No HTTPS enforcement
- No rate limiting on auth

## Codebase Challenges

The `src/index.ts` file reader returned a **fragment** starting with a comment continuation (`: Fetches remote asset bytes using axios without IP restrictions...`), suggesting the file may have been stored with a split/broken first line. Despite this, the full attack surface was reconstructable through systematic grep searches against the source, combined with complete analysis of `public/index.html`, `public/js/app.js`, `public/css/main.css`, `package.json`, `tsconfig.json`, and `Dockerfile`. The critical vulnerability chain (SSRF) was fully provable from both the commented-out code fragment in `src/index.ts` and the client-side `triggerSsrfPreview()` function in `app.js`.
