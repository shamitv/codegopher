

The chained vulnerability static audit is complete. Here's what was found:

## Audit Summary

**4 chained vulnerabilities** were identified across this Compliance Document Tracker codebase:

| Chain | Severity | Confidence | Impact |
|---|---|---|---|
| **Chain 1** — Admin token leak → eval → RCE | CRITICAL | High | Remote code execution via hardcoded admin token + `eval()` on user metadata |
| **Chain 2** — Debug endpoint → admin token → IDOR | HIGH | High | Full document exfiltration (no ownership checks on document retrieval) |
| **Chain 3** — Weak session generation → hijacking | MEDIUM | Medium | Account takeover via predictable `Math.random()` session IDs |
| **Chain 4** — eval() → database manipulation | MEDIUM-HIGH | Medium | Privilege escalation through arbitrary JS execution accessing the sessions store and SQLite db |

### Key findings:
1. **`eval()` on user-controlled metadata** in `POST /api/documents` is the single most dangerous vulnerability — it enables RCE when combined with the trivially-obtained admin token.
2. **Hardcoded admin token** (`ADMIN-DEV-TOKEN-KEY-8871`) in both the auth middleware and the debug endpoint creates two independent but complementary bypass paths.
3. **No document ownership enforcement** on `GET /api/documents/:id` — any authenticated user can read any document.
4. **Insecure session IDs** generated with `Math.random()` instead of `crypto.randomBytes()`, with missing `secure` and `sameSite` cookie flags.

### P0 fixes (do these first):
- Replace `eval()` with `JSON.parse()` (the `/safe` endpoint already does this correctly)
- Remove the hardcoded admin token bypass from `requireAuth`
- Remove or fully gate the `/api/admin/debug` endpoint in production

The full report with attack graphs, code references, remediation details, and test recommendations has been written to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`.
