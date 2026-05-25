

The chained vulnerability static audit is complete. The full report has been written to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`.

Here's a summary of findings:

### 3 Attack Chains Identified

**Chain 1 — SQL Injection → Data Exfiltration (HIGH / High Confidence)**
- `/api/packages/search?q=` directly interpolates user input into SQL via template literal. Unauthenticated, leads to full database dump including all user credentials.

**Chain 2 — Hardcoded Admin Password + MD5 → Admin Account Takeover (HIGH / High Confidence)**
- `adminpass2026` is hardcoded in plaintext in the source. All passwords use unsalted MD5 (even though `bcryptjs` is already a dependency but unused). An attacker can crack or reverse the hash, log in as admin, and control all subscriptions.

**Chain 3 — Missing CSRF Tokens + Permissive CORS → Unauthorized State Changes (MEDIUM / Medium Confidence)**
- Sessions use `httpOnly` but no `secure`, `sameSite`, or `maxAge` cookie flags. CORS allows any origin with credentials. No CSRF tokens on any POST endpoint. Enables cross-origin request forgery to log out users, change subscriptions, etc.

### 5 Cross-Cutting Weaknesses
1. Sensitive user IDs logged to stdout
2. Verbose SQLite error messages leaked to clients
3. Sessions with no TTL — never expire
4. Username enumeration via registration endpoint
5. No rate limiting on auth endpoints (compounds the weak MD5 issue)

### Key Remediation Priorities
- **P0**: Parameterize the search SQL query, replace MD5 with bcrypt, remove hardcoded credentials
- **P1**: Add CSRF protection and harden session cookie flags
- **P2**: Add rate limiting and strip error details in production
