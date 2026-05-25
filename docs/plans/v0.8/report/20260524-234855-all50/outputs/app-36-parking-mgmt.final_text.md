

The chained vulnerability static audit is complete. Here's a summary of findings:

## Audit Complete — 3 Chains Detected

### Chain 1: SQL Injection → Database Exfiltration (HIGH)
The `/api/spots/search` endpoint at `src/index.js:131-135` interpolates `req.query.q` directly into SQL via string concatenation, with no parameterization. Since the endpoint is unauthenticated, this is an open SQL injection vector enabling full database read, including user password hashes.

### Chain 2: Weak Session IDs → Account Takeover (HIGH)  
`Math.random()` at line 106 generates session IDs with only ~26 bits of entropy. Combined with in-memory sessions with no expiry (line 69), permissive CORS allowing any origin with credentials (line 13), and no rate limiting on login, this enables session hijacking and CSRF-style abuse.

### Chain 3: Client-Controlled Booking Cost → Financial Fraud (MEDIUM)
The `/api/bookings/book` endpoint accepts `total_cost` directly from the client (line 144) with no server-side recalculation or validation against the spot's `price_rate`. The developer even acknowledged this gap in a code comment (line 146).

### Cross-Cutting Weaknesses
5 additional weaknesses identified: hardcoded seed credentials, CORS misconfiguration, verbose error messages, in-memory session store with no cleanup, and no rate limiting.

The full report has been written to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`.
