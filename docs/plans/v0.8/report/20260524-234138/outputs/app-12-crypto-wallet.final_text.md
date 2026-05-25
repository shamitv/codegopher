

Report written to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`. Here's what I found:

### 3 Chained Vulnerabilities Identified

| # | Chain | Max Severity | Confidence |
|---|-------|-------------|------------|
| 1 | **IDOR → Plaintext Private Key Exposure** — Any authenticated user reads any other user's wallet (including private key) via `GET /api/wallet?userId=N` | Critical | High |
| 2 | **Hardcoded Plaintext Credentials** — Passwords `alice123` / `bob123` stored in source; login does direct `===` comparison. Source leak = all accounts compromised | Critical | High |
| 3 | **Missing CSRF + Cookie Auth** — No CSRF tokens on any mutating endpoint. `POST /api/wallet/transfer` relies solely on cookie | Medium–High | Medium |

### Key Cross-Cutting Weaknesses (8 cataloged)
- Missing `secure` flag on session cookie
- No session regeneration after login
- Frontend displays private key in plaintext
- No rate limiting on auth endpoints
- Transfer-by-address method is broken/incomplete

### All chains were written with full evidence citations including file paths, line numbers, and source snippets.
