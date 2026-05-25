

I've completed the chained vulnerability static audit and written the report to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`.

## Audit Summary

I reviewed two source files:
- **`src/index.js`** — Full Express application with SQLite database, authentication, booking endpoints, and admin functionality
- **`src/referenceGuards.js`** — Utility functions (`sameOwner`, `allowedCallback`, `normalizeIdentifier`) that are **not imported** in the main app

### 5 Chains Detected

| Chain | Severity | Confidence | Impact |
|---|---|---|---|
| **SQL Injection in `/api/spots/search`** | HIGH | HIGH | Full database exfiltration via `UNION SELECT` |
| **Weak Session IDs (`Math.random()`)** | HIGH | HIGH | Account takeover via session hijacking |
| **Permissive CORS + No CSRF** | MEDIUM-HIGH | MEDIUM | Cross-origin state changes (booking fraud) |
| **Hardcoded Admin Credentials** | HIGH | HIGH | Direct admin impersonation |
| **No Server-Side Price Validation** | MEDIUM | HIGH | Revenue loss via zero-cost bookings |

### Key Findings

1. **Critical** — Unparameterized SQL string interpolation allows UNION-based injection on a public endpoint
2. **Critical** — Non-cryptographic session IDs (`Math.random()` + `Date.now()`) enable session hijacking
3. **Critical** — Admin credentials (`admin_attendant` / `attendant2026Secure!`) hardcoded in source
4. **Important** — `origin: true` CORS config + no CSRF tokens enables cross-origin authenticated attacks
5. **Important** — Booking endpoint accepts user-supplied `total_cost` without server-side validation

### Notable Observation

The utility functions in `src/referenceGuards.js` are defined but **not used** by `src/index.js`. This suggests unused security code or potentially incomplete integration — the `allowedCallback` guard hints at a URL validation feature that isn't wired up.
