

The chained vulnerability static audit is complete. Here's a summary of findings:

## Audit Complete — 3 Chained Vulnerabilities Found

### Chain 1: Username Enumeration → Plaintext Auth Bypass → Account Takeover (CRITICAL / High Confidence)
- Login endpoint returns identical `401` error for both "user not found" and "wrong password", enabling username enumeration
- Passwords stored and compared in plaintext (`'aliceborrow123'`, etc.)
- Any valid credential pair creates an unvalidated in-memory session

### Chain 2: Weak Session IDs + Missing Cookie Flags → Session Hijacking (HIGH / High Confidence)
- `Math.random()` produces only ~30 bits of entropy — trivially guessable
- Session cookie lacks `Secure` and `SameSite` flags
- No session expiration or client binding (IP/User-Agent)

### Chain 3: Unauthenticated Debug Endpoint + Permissive CORS → Mass Credential Leakage (CRITICAL / High Confidence)
- `GET /api/debug/users` returns all users with plaintext passwords — no auth required
- `cors({ origin: true, credentials: true })` allows any origin to read responses with credentials
- Enables cross-origin harvesting of all credentials from attacker-controlled pages

### Additional Weaknesses
- **IDOR**: Any authenticated user can access any contract (`GET /api/contracts/:id`)
- **CSRF**: No CSRF protection on state-changing POST endpoints
- **Input validation**: Negative interest rates accepted on loan applications
- **Dead code**: `/api/user/settings` runs a no-op update

### P0 Remediations
1. Remove `/api/debug/users` endpoint
2. Implement bcrypt password hashing
3. Restrict CORS to known origins
4. Replace session IDs with `crypto.randomBytes(32)`
5. Add `Secure` and `SameSite='Strict'` cookie flags

The full report with Mermaid attack graphs, line-level evidence, and a priority-ordered remediation matrix has been written to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`.
