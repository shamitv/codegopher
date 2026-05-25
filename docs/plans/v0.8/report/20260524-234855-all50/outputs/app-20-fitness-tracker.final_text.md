

The audit is complete. Here's the final summary:

## Chained Vulnerability Audit Complete

### Report Written
`docs/security/CHAINED_VULNERABILITIES_REVIEW.md`

### Chain Summary (4 chains)

| # | Severity | Description |
|---|---|---|
| 1 | **HIGH** | Hardcoded seed passwords (`coach2026Secure!`, etc.) + `Math.random()` session IDs + no rate limiting → full admin account takeover |
| 2 | **MEDIUM** | IDOR on `GET /api/activities/:id` — query lacks `user_id` ownership check → cross-user activity data leakage |
| 3 | **MEDIUM** | Prototype pollution via `unsafeMerge` on untrusted `req.body.customSettings` → app DoS / config corruption |
| 4 | **LOW** | CORS `origin: true` + `credentials: true` + zero CSRF tokens → CSRF-mediated forced logout |

### Key Remediations

| Priority | Action |
|---|---|
| **P0** | Remove hardcoded seed passwords; use env vars |
| **P0** | Replace `Math.random()` with `crypto.randomUUID()` |
| **P1** | Add `AND user_id = ?` to the `:id` activity query |
| **P1** | Replace `unsafeMerge` with whitelist-based config update |
| **P2** | Pin CORS origin to allowlist; add `SameSite=Strict` |
| **P2** | Add login rate limiting |

### Methodology
- **Static-only**: Source, config, and Dockerfile reviewed only. No live probes or exploit scripts.
- **Cross-cutting weaknesses**: User enumeration, in-memory DB, no HTTPS enforcement, no input validation.
- **Tests recommended**: Session predictability, IDOR, prototype pollution, CSRF, CORS, rate limiting, username enumeration.
