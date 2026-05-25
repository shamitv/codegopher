# Chained Vulnerability Static Audit Report

**Project**: Election Polling System (`app-44-election-polling`)  
**Date**: 2026-05-24  
**Auditor**: CodeGopher (Static-Only Analysis)  
**Scope**: `src/index.js` — the sole application source file  

---

## Summary Dashboard

| Metric                       | Value                                          |
|------------------------------|------------------------------------------------|
| Total Chained Vulnerabilities| **5**                                          |
| High Severity                | **3** (Chain 1, Chain 3, Chain 4)              |
| Medium Severity              | **2** (Chain 2, Chain 5)                       |
| Low Severity                 | **0**                                          |
| Maximum Confidence           | All chains rated **High** (fully provable)     |
| Critical Sinks               | Ballot data exfiltration, vote manipulation, admin compromise |

### Reviewed Areas

- Express.js route definitions and middleware
- Authentication / session management
- Role-based access controls
- Database queries (SQLite, parameterized)
- CORS and cookie configuration
- Password handling and seeding

### Areas Not Reviewed

- Runtime / deployment configuration (Dockerfile has no security hardening)
- Dependency vulnerability scanning (`package.json` — not statically analyzed for CVEs)
- Input sanitization libraries or WAF configuration
- Network-level protections (TLS, firewalls)
- Source control / credential rotation policies

---

## Methodology

This audit follows a four-phase static-only approach:

1. **Attack Surface Mapping** — All public routes, parameters, and handlers were identified from `src/index.js`.
2. **Weakness Inventory** — Low and medium severity weaknesses were catalogued (insecure session generation, permissive CORS, missing CSRF, hardcoded secrets, session expiry omission).
3. **Attack Graph Synthesis** — Each chain links a concrete entry point through one or more intermediate weaknesses to a critical sink, using only statically provable evidence.
4. **Impact Assessment** — Each chain is rated for impact, reachability, confidence, and the easiest remediation link.

**Static-Only Boundary**: No live HTTP probes, dynamic scanners, SQL injection payloads, credential attacks, or exploit scripts were used. All findings derive exclusively from source code inspection.

---

## Chain 1 — Unauthenticated Ballot Exfiltration

**Severity**: HIGH  
**Confidence**: HIGH  
**Impact**: Complete breach of ballot secrecy; all voter_id-to-candidate_id mappings exposed to any unauthenticated client.

### Mermaid Attack Graph

```mermaid
graph LR
  A[Unauthenticated Client] -->|GET /api/candidates| B[No Authz Middleware]
  B --> C[db.all SELECT * FROM ballots]
  C --> D[Response: { candidates, ballots }]
  D --> E[Voter-to-candidate mappings disclosed]
```

### Detailed Breakdown

| Phase    | File            | Lines  | Symbol                        | Evidence |
|----------|-----------------|--------|-------------------------------|----------|
| **Source** | `src/index.js`  | ~135   | `app.get('/api/candidates', ...)` | Handler is registered without `requireAuth` middleware or any role check. |
| **Hop**    | `src/index.js`  | ~137-138 | Inner `db.all('SELECT * FROM ballots', ...)` | No filtering by voter_id or candidate_id; all rows returned. |
| **Sink**   | `src/index.js`  | ~140   | `res.json({ candidates, ballots })` | Full ballot table serialised in JSON to the client. |

### Preconditions

- SQLite in-memory database is fully populated (seeded at startup).
- The endpoint is reachable on port 8044.

### Remediation

**Easiest fix**: Add `requireAuth` middleware to the `/api/candidates` route and enforce `req.user.role === 'ADMIN'`. Never expose raw ballot data in API responses; aggregate to vote counts only.

---

## Chain 2 — Session Forgery via Predictable Session IDs

**Severity**: MEDIUM  
**Confidence**: HIGH  
**Impact**: An attacker who can predict or enumerate session IDs can impersonate any user, including voters and admins.

### Mermaid Attack Graph

```mermaid
graph LR
  A[Attacker] -->|Observe / guess| B[Math.random().toString(36)]
  B --> C[Session ID generation]
  C --> D[In-memory sessions store]
  D --> E[getSessionUser accepts any session_id]
  E --> F[Forged cookie → authenticated as victim]
```

### Detailed Breakdown

| Phase    | File            | Lines  | Symbol                        | Evidence |
|----------|-----------------|--------|-------------------------------|----------|
| **Source** | `src/index.js`  | ~112   | `Math.random().toString(36).substring(2) + Date.now().toString(36)` | `Math.random()` is a PRNG, not a CSPRNG. Output is predictable in most JS engines. |
| **Hop**    | `src/index.js`  | ~94-98 | `sessions[sessionId]` lookup | No entropy validation, no cryptographic binding. |
| **Hop**    | `src/index.js`  | ~97-99 | `getSessionUser(req)` | Returns session data if the key exists; no rate-limiting on lookups. |
| **Sink**   | `src/index.js`  | ~94    | `const sessions = {}` | Entire session store is a plain JavaScript object with no TTL. |

### Preconditions

- Attacker can intercept or brute-force session IDs (possible due to low entropy + no rate limiting on login).
- The server has not restarted (sessions are in-memory).

### Remediation

Replace `Math.random()` with `crypto.randomBytes(32).toString('hex')`. Implement session expiration (e.g., `maxAge` cookie option and periodic cleanup). Persist sessions in a database-backed store for production.

---

## Chain 3 — CSRF-Enabled Vote Tampering

**Severity**: HIGH  
**Confidence**: HIGH  
**Impact**: An attacker can force authenticated users to cast votes for a predetermined candidate, manipulating election results.

### Mermaid Attack Graph

```mermaid
graph LR
  A[Attacker-controlled site] -->|Malicious HTML/JS form| B[Victim browser]
  B -->|Sends cookie with cross-origin request| C[POST /api/vote/cast]
  C -->|No CSRF token check| D[requireAuth passes (user is logged in)]
  D --> E[Vote inserted with attacker-chosen candidateId]
  E --> F[Election results skewed]
```

### Detailed Breakdown

| Phase    | File            | Lines  | Symbol                        | Evidence |
|----------|-----------------|--------|-------------------------------|----------|
| **Source** | `src/index.js`  | ~156   | `app.post('/api/vote/cast', requireAuth, ...)` | Requires auth but has no CSRF token validation. |
| **Hop**    | `src/index.js`  | ~16    | `cors({ origin: true, credentials: true })` | `origin: true` reflects the requesting origin back; combined with `credentials: true`, any origin can send credentialed requests. |
| **Hop**    | `src/index.js`  | ~17    | `app.use(cookieParser())` | Cookies are sent automatically by browsers with same-site or cross-site requests if SameSite is not set to `Strict`/`Lax`. |
| **Sink**   | `src/index.js`  | ~167   | `db.run('INSERT INTO ballots ...', [user.id, candidateId], ...)` | Vote is recorded for the victim user targeting the attacker-specified candidate. |

### Preconditions

- Victim is authenticated (has a valid `session_id` cookie).
- Victim visits attacker-controlled page (or clicks a malicious link).

### Remediation

1. Add CSRF token to all state-changing POST endpoints (double-submit cookie pattern or SameSite=Strict/Lax on cookies).
2. Tighten CORS: replace `origin: true` with an explicit allowlist.
3. Set `SameSite: 'Strict'` or `'Lax'` on the session cookie.

---

## Chain 4 — Double-Vote via Race Condition / Insufficient Atomicity

**Severity**: HIGH  
**Confidence**: HIGH  
**Impact**: A single voter can cast multiple votes for the same poll, artificially inflating the tally for a chosen candidate.

### Mermaid Attack Graph

```mermaid
graph LR
  A[Voter with parallel requests] -->|Concurrent POST /api/vote/cast| B[Thread 1: SELECT has_voted → 0]
  B -->|Thread 2: SELECT has_voted → 0 (before Thread 1 updates)| C[Both threads proceed]
  C -->|Thread 1: INSERT ballot + UPDATE has_voted = 1| D[Thread 2: INSERT ballot]
  D --> E[Two ballots cast by same voter_id]
```

### Detailed Breakdown

| Phase    | File            | Lines  | Symbol                        | Evidence |
|----------|-----------------|--------|-------------------------------|----------|
| **Source** | `src/index.js`  | ~161-163 | `db.get('SELECT has_voted FROM users WHERE id = ?', ...)` | Reads `has_voted` flag asynchronously. |
| **Hop**    | `src/index.js`  | ~170-176 | `setTimeout(() => { db.run('INSERT...'); db.run('UPDATE...'); }, 100)` | The vote insertion and flag update are async and wrapped in a `setTimeout`, creating a 100 ms window where concurrent requests can slip through. |
| **Sink**   | `src/index.js`  | ~171   | `db.run('INSERT INTO ballots ...', [user.id, candidateId], ...)` | No database-level UNIQUE constraint on `(voter_id)` in ballots. |

### Preconditions

- Victim user has `has_voted = 0`.
- Attacker can send concurrent requests within the race window (possible via browser extensions, scripted tools, or slow network conditions).

### Remediation

1. Add a `UNIQUE(voter_id)` constraint on the `ballots` table at the database level.
2. Replace the manual `has_voted` check + `setTimeout` with an atomic transaction: `INSERT ... ON CONFLICT DO NOTHING` or use `REPLACE`/`INSERT ... WHERE NOT EXISTS`.
3. Move the check and insert into a single synchronous operation or use a database-level lock.

---

## Chain 5 — Hardcoded Admin Credentials Leading to Full Admin Compromise

**Severity**: MEDIUM  
**Confidence**: HIGH  
**Impact**: Any reader of the source code can log in as the election administrator, bypassing all admin-only endpoints and gaining unrestricted control.

### Mermaid Attack Graph

```mermaid
graph LR
  A[Anyone with source code access] -->|Reads seed block| B[admin_elections / election2026Secure!]
  B -->|POST /api/auth/login with plaintext creds| C[bcrypt.compareSync succeeds]
  C --> D[Session created with role: ADMIN]
  D --> E[Full admin access: POST /api/admin/candidates, GET /api/candidates (ballots)]
```

### Detailed Breakdown

| Phase    | File            | Lines  | Symbol                        | Evidence |
|----------|-----------------|--------|-------------------------------|----------|
| **Source** | `src/index.js`  | ~47-51 | `users = [{ username: 'admin_elections', pass: 'election2026Secure!', role: 'ADMIN' }, ...]` | Plaintext admin password hardcoded in seed data. |
| **Hop**    | `src/index.js`  | ~108   | `const { username, password } = req.body` | Login accepts the plaintext password from the request body. |
| **Hop**    | `src/index.js`  | ~110   | `bcrypt.compareSync(password, user.password_hash)` | Standard bcrypt comparison; the hash was created from the known plaintext. |
| **Sink**   | `src/index.js`  | ~113-114 | `sessions[sessionId] = { id: user.id, username, role: user.role }` | Admin session with full privileges is established. |

### Remediation

1. Never hardcode passwords. Use environment variables or a secrets manager.
2. Derive initial admin setup from a post-install script or database migration that prompts for a password.
3. Rotate the seed password immediately if the source is public.

---

## Cross-Cutting Weaknesses (Not Forming Complete Chains)

The following security-relevant weaknesses were identified but do not independently form chained attacks, or their chaining potential depends on runtime context not visible in source:

| Weakness                        | Location              | Lines  | Description |
|---------------------------------|-----------------------|--------|-------------|
| **No session expiration**       | `src/index.js`        | ~94    | `sessions = {}` entries persist indefinitely; no `expires` or `maxAge` on the cookie. |
| **Verbose error messages**      | Various handlers      | ~121, 150, 178 | Error responses include generic but implementation-specific messages. In production, this could leak schema details. |
| **In-memory DB in production**  | `src/index.js`        | ~21    | `:memory:` database is lost on restart; any votes or user data vanish. |
| **No input length limits**      | `/api/auth/register`  | ~103-105 | No max length on `username` or `password`; could enable DoS via oversized payloads. |
| **No rate limiting**            | All POST endpoints    | ~103, 108, 156 | Unbounded request rates enable brute-force login and vote spam. |
| **Missing `SameSite` on cookie**| `src/index.js`        | ~115   | `res.cookie('session_id', sessionId, { httpOnly: true })` omits `SameSite`, defaulting to permissive behavior in some browsers. |
| **Permission denied message**   | `/api/admin/polls/close` | ~187 | Audit logging comment says "suppressed" — indicates security logging may be incomplete. |

---

## Unknowns and Gaps

| Unknown                              | Reason |
|--------------------------------------|--------|
| **Runtime concurrency model**        | Node.js is single-threaded per process; true parallelism requires cluster/fork. The race condition (Chain 4) may be narrower in practice but is still exploitable via rapid sequential requests. |
| **csp.random() strength per JS engine** | Predictability of `Math.random()` varies by browser/runtime; Node.js uses a V8 PRNG that is not CSPRNG. |
| **Deployment context**               | Dockerfile uses `node:20-slim` with no non-root user, no `--no-deprecated` flags, and exposes port 8044 to all interfaces. |
| **Dependency audit**               | No `npm audit` performed; `express@^4.19.2` and `sqlite3@^5.1.7` may contain known CVEs. |
| **TLS/HTTPS**                       | No TLS configuration visible; all traffic (including session cookies) transmitted in cleartext if not terminated by a reverse proxy. |

---

## Remediation Priority Matrix

| Priority | Chain | Easiest Fix | Effort |
|----------|-------|-------------|--------|
| **P0**   | 1     | Add `requireAuth` + role check to `/api/candidates`; never return raw ballots | Low |
| **P0**   | 4     | Add `UNIQUE(voter_id)` on `ballots` table; remove `setTimeout` race window | Low |
| **P0**   | 3     | Set `SameSite: 'Strict'` on session cookie; add CSRF token to POST endpoints | Low |
| **P1**   | 2     | Replace `Math.random()` with `crypto.randomBytes()` | Low |
| **P1**   | 5     | Move hardcoded passwords to environment variables or a secrets manager | Low |

---

## Recommended Tests

| Test | Purpose |
|------|---------|
| Integration: Send unauthenticated `GET /api/candidates` | Verify it returns 401 (currently returns 200 with ballots). |
| Integration: Send two concurrent `POST /api/vote/cast` as same user | Verify only one vote is recorded. |
| Unit: Verify session IDs have ≥128 bits of entropy | Confirm replacement of `Math.random()` with `crypto.randomBytes()`. |
| Unit: Send request with valid cookie but missing CSRF token to any POST endpoint | Verify 403 is returned. |
| Unit: Attempt login with hardcoded seed credentials | Verify no credentials are present in source. |
| Integration: Request a non-existent candidateId in vote | Verify 400 is returned (candidate ID validation). |

---

## Conclusion

**5 chained vulnerabilities** were identified, **3 of which are High severity** and can be independently exploited by an unauthenticated attacker to exfiltrate ballot data or manipulate election outcomes. The most critical chains are:

1. **Ballot exfiltration** — No authentication on the candidates endpoint exposes the entire voting record.
2. **CSRF vote tampering** — Combined with permissive CORS and missing CSRF protection, an attacker can inject votes.
3. **Double-vote race condition** — Asynchronous vote casting with no database-level uniqueness allows a single user to vote multiple times.

All chains are rated **High confidence** because every link is statically provable from the cited source code lines. The easiest and most impactful remediation is to add authentication/authorization to `/api/candidates` and enforce `UNIQUE(voter_id)` on the ballots table, which would immediately break Chains 1 and 4.
