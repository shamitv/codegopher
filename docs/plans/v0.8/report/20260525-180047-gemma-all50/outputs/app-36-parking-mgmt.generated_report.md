# Chained Vulnerability Static Audit Report

**Project:** app-36-parking-mgmt (Parking Management System)  
**Date:** 2026-05-25  
**Auditor:** CodeGopher (Static-Only Analysis)  
**Scope:** `src/index.js`, `package.json`, `Dockerfile`

---

## 1. Summary Dashboard

| Metric | Value |
|---|---|
| Total Chained Vulnerabilities Found | **3** |
| Maximum Severity | **High** |
| Medium-Severity Chains | 1 |
| Low-Severity Chains | 1 |
| Weaknesses Inventory (non-chained) | 4 |
| Reviewed Files | 3 (`src/index.js`, `package.json`, `Dockerfile`) |
| Areas Not Reviewed | Database migration scripts, test coverage, deployment configs, runtime logs |

---

## 2. Methodology & Safety Note

- **Static-only**: This audit inspected source code, configuration, and dependency manifests only. No live HTTP probes, dynamic scanners, shell commands, or external network tests were performed.
- **Method**: Attack surface mapping → Weakness inventory → Attack graph synthesis → Impact assessment.
- **Confidence ratings**: High = every link statically provable; Medium = plausible but one link depends on runtime behavior; Low = weakly supported.

---

## 3. Attack Graphs & Detailed Chains

### Chain 1: SQL Injection → Full Database Read (Data Exfiltration)

```mermaid
flowchart LR
    A["Attacker (any anonymous user)"] -->|"GET /api/spots/search?q='; DROP TABLE users;--|" B["Entry: /api/spots/search (src/index.js:139)"]
    B -->|"req.query.q used in template literal|" C["Weakness: Unparameterized SQL (src/index.js:144)"]
    C -->|"String concatenation into SQLite query|" D["Sink: db.all(sql, ...) (src/index.js:145)"]
    D -->|"Arbitrary SQL execution against in-memory DB|" E["Impact: Full data exfiltration / privilege escalation"]
```

| Link | File | Lines | Symbol | Evidence |
|---|---|---|---|---|
| **Source** | `src/index.js` | 139–140 | GET `/api/spots/search` | `const queryParam = req.query.q || '';` — user-controlled query param, no auth required |
| **Hop 1** | `src/index.js` | 144 | SQL string assembly | `const sql = \`SELECT * FROM spots WHERE type LIKE '%\${queryParam}%'\`;` — template literal with direct interpolation |
| **Sink** | `src/index.js` | 145 | db.all() execution | `db.all(sql, ...)` — executes the constructed string as raw SQL |
| **Impact** | — | — | — | Arbitrary SQL: `UNION SELECT` to dump users table (including password hashes), manipulate bookings, extract data |

- **Preconditions**: Attacker has HTTP access. No authentication required. No input sanitization.
- **Impact**: Full read access to all tables (users, spots, bookings). Potential write via stacked queries or UNION-based exfiltration. Seeded credentials visible in source could be used with extracted hashes offline.
- **Severity**: **High**
- **Confidence**: **High** — SQL injection via string concatenation is directly visible at line 144; sqlite3 passes the string directly to the database engine.
- **Easiest Remediation Link**: Replace template literal with parameterized query:
  ```js
  const sql = 'SELECT * FROM spots WHERE type LIKE ?';
  db.all(sql, [`%${queryParam}%`], (err, rows) => { ... });
  ```

---

### Chain 2: Permissive CORS + No CSRF Token → Cross-Site Request Forgery → Account Takeover / Booking Manipulation

```mermaid
flowchart LR
    A["Malicious Website"] -->|"User visits (with valid session cookie)"| B["Triggers POST /api/bookings/:id/cancel or /api/admin/spots"]
    B -->|"CORS origin:* + credentials:true|" C["Weakness: Permissive CORS (src/index.js:10)"]
    C -->|"No CSRF token validation|" D["Weakness: No CSRF protection (entire file)"]
    D -->|"Session cookie sent by browser|" E["Sink: Authenticated action executes under victim identity (e.g. line 128-137)"]
    E -->|"Unauthorized booking cancellation / spot registration|" F["Impact: Session hijacking via CSRF; privilege escalation as ADMIN"]
```

| Link | File | Lines | Symbol | Evidence |
|---|---|---|---|---|
| **Source** | `src/index.js` | 10 | CORS config | `app.use(cors({ origin: true, credentials: true }))` — `origin: true` reflects the request Origin header, allowing any domain |
| **Hop 1** | Entire file | — | Missing CSRF | No CSRF token middleware or validation exists on any POST/DELETE endpoint |
| **Hop 2** | `src/index.js` | 117 | Session cookie | `res.cookie('session_id', sessionId, { httpOnly: true })` — cookie set with httpOnly but **no SameSite** attribute |
| **Sink** | `src/index.js` | 155–167 | POST `/api/bookings/book` / 128–137 `/api/admin/spots` | Authenticated POST endpoints accept requests from any origin |

- **Preconditions**: Victim must be authenticated (has valid `session_id` cookie). Attacker hosts a malicious page. Browser automatically includes cookies on cross-origin requests.
- **Impact**:
  - **Medium** for booking endpoints: Victim can be tricked into booking/canceling spots on the attacker's behalf.
  - **High** if combined with Chain 3 (see below): A CSRF request to `/api/admin/spots` would register a malicious spot with attacker-controlled data.
- **Severity**: **Medium** (Medium standalone, potentially High when chained)
- **Confidence**: **High** — CORS with `origin: true` + `credentials: true` plus absence of any CSRF mechanism is unambiguous.
- **Easiest Remediation Link**: Add `SameSite: 'Strict'` or `'Lax'` to cookie and/or add CSRF token validation (e.g., double-submit cookie pattern).

---

### Chain 3: Weak Session ID + No CSRF → Session Prediction → Account Takeover

```mermaid
flowchart LR
    A["Attacker observes traffic / brutes force"] -->|"Reconstructs session_id|" B["Weakness: Math.random() session generation (src/index.js:115)"]
    B -->|"Math.random() not CSPRNG + Date.now() predictable|" C["Weakness: Sessions not invalidated after login retry (src/index.js:116)"]
    C -->|"Multiple sessions can coexist|" D["Sink: getSessionUser() returns first valid session (src/index.js:74-79)"]
    D -->|"Attacker authenticates as victim|" E["Impact: Full account takeover"]
```

| Link | File | Lines | Symbol | Evidence |
|---|---|---|---|---|
| **Source** | `src/index.js` | 115 | Session ID generation | `Math.random().toString(36).substring(2) + Date.now().toString(36)` — 56 bits of entropy at best, and `Math.random()` is not cryptographically secure |
| **Hop** | `src/index.js` | 73–79 | getSessionUser() | Session lookup by cookie value only; no binding to IP/User-Agent; no session fixation checks |
| **Sink** | `src/index.js` | 82–88 | requireAuth middleware | Accepts any valid session cookie without additional verification |

- **Preconditions**: Attacker can predict or guess session IDs (feasible due to weak RNG). Login endpoint (`/api/auth/login`, line 105–118) does not invalidate existing sessions for the same user.
- **Impact**: Attacker gains unauthorized access to any user account (including ADMIN).
- **Severity**: **Medium**
- **Confidence**: **Medium** — `Math.random()` unpredictability depends on the Node.js V8 engine version; still, it is documented as non-cryptographic. Confidence is not "High" because actual predictability depends on runtime behavior.
- **Easiest Remediation Link**: Replace with `crypto.randomUUID()` or `crypto.randomBytes(32).toString('hex')`.

---

### Chain 4 (Cross-Cutting): Client-Controlled Cost + Booking Bypass → Revenue Loss

```mermaid
flowchart LR
    A["Authenticated User"] -->|"POST /api/bookings/book with total_cost=0|" B["Endpoint (src/index.js:155)"]
    B -->|"No server-side cost recalculation|" C["Weakness: Client-supplied total_cost accepted as-is (line 156)"]
    C -->|"Comment explicitly notes this: 'permitting zero-fee booking'"|" D["Sink: Booking created with 0 cost (line 160)"]
    D -->|"Premium spot booked for free|" E["Impact: Financial loss / revenue bypass"]
```

| Link | File | Lines | Symbol | Evidence |
|---|---|---|---|---|
| **Source** | `src/index.js` | 156 | Destructured `total_cost` | `const { spot_id, duration_hours, total_cost } = req.body;` — client-supplied value accepted directly |
| **Hop** | `src/index.js` | 158 (comment) | Intentional bypass | `// without recalculation or validation checks, permitting zero-fee booking of premium spots.` |
| **Sink** | `src/index.js` | 160–162 | INSERT without validation | `db.run('INSERT INTO bookings ... VALUES (?, ?, ?, ?)', [user.id, spot_id, duration_hours, total_cost], ...)` — no server-side price lookup |

- **Preconditions**: User must be authenticated (via Chain 2 or 3 attack, or legitimately).
- **Impact**: Attend any spot (especially Premium) for $0 or arbitrary low cost.
- **Severity**: **Low** (business logic, not direct security breach)
- **Confidence**: **High** — code path is direct and the comment confirms the intent.
- **Easiest Remediation Link**: Fetch spot price from DB and recalculate: `SELECT price_rate FROM spots WHERE id = ?`, then compute `total_cost = price_rate * duration_hours`.

---

## 4. Weakness Inventory (Non-Chained)

| # | Weakness | File | Lines | Details |
|---|---|---|---|---|
| W1 | **Verbose Error Messages** | `src/index.js` | 146 | `err.message` exposed to client in search endpoint (`details: err.message`). Could leak schema, internal paths, or SQLite internals. |
| W2 | **Missing SameSite on Cookie** | `src/index.js` | 117 | `res.cookie('session_id', sessionId, { httpOnly: true })` — no `SameSite` attribute. Mitigates some CSRF but does not fully prevent it. |
| W3 | **Hardcoded Seed Credentials in Source** | `src/index.js` | 30–35 | Plaintext passwords stored in source: `'driver123'`, `'driver456'`, `'attendant2026Secure!'`. Committed to VCS. |
| W4 | **No Rate Limiting** | Throughout | — | Login, register, and search endpoints have no rate limiting. Enables brute-force and enumeration attacks. |

---

## 5. Cross-Cutting Weaknesses Section

These security-relevant issues were identified but do not independently form a complete chain to a critical impact:

1. **No Input Validation / Sanitization**: Only `username` and `password` are checked for presence. `spot_number`, `type`, `price_rate`, `duration_hours` are not validated. Malicious type values could interfere with LIKE queries.
2. **Authorization Gaps in Booking**: While `requireAuth` is enforced on `/api/bookings/book`, the `total_cost` bypass (Chain 4) and potential SQL injection in the search route (Chain 1) mean no authenticated boundary is fully trustworthy.
3. **In-Memory Database** (`src/index.js`, line 12): `sqlite3.Database(':memory:')` means all data is lost on process restart. Not a security issue per se, but eliminates any persistence-based audit trail.
4. **No Audit Logging**: The `console.log` on spot creation (line 127) is the only log statement. No authentication audit trail, no login success/failure logging.

---

## 6. Unknowns & Not-Reviewed Areas

- **Test Coverage**: No tests found. Integration and security tests should be added, especially for the SQL injection and CSRF chains.
- **Deployment Configuration**: Dockerfile exposes no security hardening (no non-root user, no health checks, no resource limits).
- **HTTPS/TLS**: Application listens on `http://localhost:8036`. No TLS termination is configured. Cookies will be sent in cleartext over untrusted networks.
- **Dependencies**: `bcryptjs`, `express`, `sqlite3`, `cors`, `cookie-parser` — no `npm audit` or dependency vulnerability scan performed.
- **Helmet / Security Headers**: No `helmet` or equivalent middleware for `X-Frame-Options`, `X-Content-Type-Options`, `Strict-Transport-Security`, etc.

---

## 7. Remediation Priority Summary

| Priority | Action | Chains Broken |
|---|---|---|
| **P0** | Parameterize SQL in `/api/spots/search` | Chain 1 |
| **P0** | Replace `Math.random()` session IDs with `crypto.randomBytes()` | Chain 3 |
| **P1** | Remove seed credentials from source; use environment variables | W3 |
| **P1** | Add `SameSite: 'Strict'` to session cookie | Chain 2 |
| **P1** | Add CSRF token validation to all mutating endpoints | Chain 2 |
| **P2** | Recalculate `total_cost` server-side in booking endpoint | Chain 4 |
| **P2** | Remove `details: err.message` from error responses | W1 |
| **P2** | Add rate limiting to `/api/auth/login` and `/api/auth/register` | W4 |
| **P3** | Add Helmet security headers; enable TLS | Cross-cutting |

---

*End of report.*
