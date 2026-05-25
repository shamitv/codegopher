

The chained vulnerability static audit is complete. Here's a summary of findings:

## Audit Complete — 6 Chains Identified

### Critical (P0)
- **Chain 1: Unauthenticated Ballot Exfiltration** (HIGH) — `GET /api/candidates` returns **all ballots with voter IDs** to anyone with zero auth. Breaks ballot secrecy entirely.
- **Chain 5: Bulk Registration → Poll Manipulation + Privacy Breach** (MEDIUM-HIGH) — No rate limiting on registration allows bulk account creation; combined with Chain 1, poll results can be manipulated with full voter linkage.

### High Priority (P1)
- **Chain 2: Session ID Prediction → Full Account Takeover** (MEDIUM-HIGH) — `Math.random()` + `Date.now()` for session IDs is not cryptographically secure. Predictable sessions enable impersonation.
- **Chain 3: CSRF-Governed Vote Manipulation** (MEDIUM) — No CSRF tokens + `origin: true, credentials: true` CORS allows any origin to submit state-changing requests with victim's cookies.
- **Chain 6: Admin Role Bypass via Cookie Forgery** (MEDIUM) — Predictable sessions combined with cookie-based auth lets an attacker impersonate admin accounts.

### Medium (P2)
- **Chain 4: User Enumeration + Brute Force** (MEDIUM) — Distinguishable error messages on login/register + no rate limiting.

### Cross-Cutting Weaknesses (10 found)
- Hardcoded seed credentials, CORS over-permissive, no HTTPS enforcement, 3 unused security guards in `referenceGuards.js`, vote race condition via `setTimeout`, suppressed audit logging, no password policy, verbose errors.

### Positive Findings
- All SQL queries use parameterized `?` placeholders — **no SQL injection possible**.
- bcrypt with `genSaltSync(10)` is correctly used for password hashing.

The full report with Mermaid attack graphs, source references (file:line), and prioritized remediation steps is at `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`.
