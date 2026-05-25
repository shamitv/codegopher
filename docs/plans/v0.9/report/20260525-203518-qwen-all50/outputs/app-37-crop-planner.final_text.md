

The chained vulnerability static audit is complete. Here's a summary of what was found:

## Audit Results

**4 vulnerability chains** were identified across the codebase:

| Chain | Severity | Confidence | Description |
|-------|----------|------------|-------------|
| **1** | **High** | High | **SSRF → Token Leak → Data Exfiltration** — An authenticated user can use the SSRF-prone `/api/weather/proxy` endpoint to reach internal services, first harvesting the plaintext API token from the unauthenticated debug config endpoint, then using it to exfiltrate the entire `crops` table. |
| **2** | Medium | Medium | **ZIP Path Traversal → Arbitrary File Write** — The `/api/crop-plan/import-layout` endpoint extracts user-uploaded ZIP files without validating `entryName` against path traversal, allowing writes outside the intended `layouts/` directory. |
| **3** | Medium | Medium | **Weak Session IDs + Permissive CORS → Session Hijacking** — Session IDs are generated with `Math.random()` (non-cryptographic) and CORS is configured with `origin: true` + `credentials: true`, enabling session hijacking and cross-origin cookie theft. |
| **4** | Medium | Medium | **Permissive CORS + No CSRF → State Modification** — All POST endpoints lack CSRF protection and accept credentialed cross-origin requests from any domain. |

**Key cross-cutting weaknesses** include hardcoded debug credentials in plaintext, no rate limiting, an in-memory session store with no expiration, verbose error messages leaking internal data, and several security utility functions in `referenceGuards.js` that are defined but never used.

The full report has been written to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md` with Mermaid attack graphs, line-level code references, and prioritized remediation steps.
