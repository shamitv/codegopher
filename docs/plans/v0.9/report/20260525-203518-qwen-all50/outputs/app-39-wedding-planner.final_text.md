

The chained vulnerability audit is complete. Here's a summary of what was found:

---

### 3 Chains Identified

| Chain | Severity | Confidence | Description |
|---|---|---|---|
| **CH-01** | High | High | MD5 (unsalted) password hashing + hardcoded seed credentials → offline brute-force → full account takeover |
| **CH-02** | Medium | Medium | Missing object-level ownership checks on event/guest endpoints → ID enumeration → cross-user PII exfiltration |
| **CH-03** | Medium | High | `Math.random()` session IDs (not cryptographically secure) → session fixation/hijacking |

### 6 Cross-Cutting Weaknesses (Not Full Chains)

- **WC-1**: Hardcoded plaintext credentials in source
- **WC-2**: Overly permissive CORS (`origin: true` + `credentials: true`)
- **WC-3**: No CSRF protection on any POST endpoint
- **WC-4**: No email/name input validation (SQL injection mitigated by parameterized queries, but other injection risks remain)
- **WC-5**: No rate limiting on auth endpoints
- **WC-6**: Security helpers in `referenceGuards.js` (`sameOwner`, `allowedCallback`) are never imported or used

### Key Observation
The `referenceGuards.js` file contains a `sameOwner()` function that would have **broken Chain 2** if it had been wired into the event-scoped routes. The security utility exists but was never integrated — a gap between security intent and implementation.

### P0 Remediations
1. Replace MD5 with `bcryptjs` (already a dependency) and remove hardcoded credentials
2. Use `crypto.randomBytes()` for session IDs; add `secure`/`sameSite` cookie flags
3. Add ownership verification on all event/guest endpoints using `sameOwner()`

The full report with Mermaid attack graphs, code references, line numbers, and remediation steps is at `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`.
