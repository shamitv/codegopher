# Chained Vulnerability Audit Report — IoT Dashboard

**Date:** 2026-05-24  
**Project:** IoT Device Dashboard (`app-17-iot-dashboard`)  
**Files Reviewed:** `src/index.js`, `package.json`, `Dockerfile`  
**Auditor:** CodeGopher (Static-Only Chained Vulnerability Review)

---

## Summary Dashboard

| Metric                  | Value                        |
|-------------------------|------------------------------|
| **Chains Detected**     | **3**                        |
| **Maximum Severity**    | **HIGH**                     |
| **Confidence Levels**   | 2 High, 1 Medium             |
| **Review Scope**        | Express API routes, DB layer, auth, external HTTP calls |
| **Static-Only Note**    | No live probes, scanners, or external network tests were performed |

### Chain Count by Severity

| Severity | Count |
|----------|-------|
| HIGH     | 1     |
| MEDIUM   | 2     |

---

## Methodology

This audit follows the **Chained Vulnerability Static Audit** framework:

1. **Attack Surface Mapping** — Identified all public and internal API routes, cookie/session mechanisms, and external HTTP callers.
2. **Weakness Inventory** — Catalogued individually modest security weaknesses (information leakage, SSRF-prone fetches, missing authorization guards, etc.).
3. **Attack Graph Synthesis** — Connected sources → weaknesses → sinks using only static evidence from the source code.
4. **Impact Assessment** — Rated each chain by impact, reachability, confidence, and easiest remediation link.

> **Static-Only Safety Boundary:** No live HTTP probes, fuzzers, SQL injection payloads, credential attacks, dynamic scanners, or external network tests were executed.

---

## Chained Vulnerability 1 — Stack Trace + Internal Secret Leak via Device Command Error Path

### Severity: HIGH | Confidence: HIGH

### Mermaid Attack Graph

```mermaid
flowchart LR
    A["Authenticated User (any role)\nsrc/index.js:129"] -->|"POST /api/devices/command\nwith TRIGGER-ERROR payload"| B["Error thrown\nsrc/index.js:136"]
    B -->|"catch block returns\n500 with stack trace\nsrc/index.js:140-146"| C["Stack trace +\ngateway_config block\nsrc/index.js:142-145"]
    C -->|"Leaked: telemetry_access_key,\ntelemetry_server_url,\ndebug_mode\nsrc/index.js:143-144"| D["Attacker obtains\ntelemetry secret token"]
    D -->|"Auth header: x-telemetry-token\nor query: ?token\nGET /api/internal/telemetry\nsrc/index.js:150"| E["Internal telemetry endpoint\nreturns ALL device keys\nsrc/index.js:157-160"]
    E -->|"Full device secret keys\nand system metadata"| F["Impact: Full device\ncompromise / lateral movement")
```

### Chain Breakdown

| Link | Type | File | Lines | Symbol | Evidence |
|------|------|------|-------|--------|----------|
| **Source** | Unrestricted authenticated input | `src/index.js` | 129-146 | `app.post('/api/devices/command'…)` | Route protected only by `requireAuth` — any authenticated user (including 'CUSTOMER') can send commands. |
| **Hop 1** | Verbose error response exposes secrets | `src/index.js` | 140-146 | Error `catch` handler | On any error, `res.status(500)` returns `error`, `stack`, **and** a `gateway_config` object containing the plaintext telemetry secret `INTERNAL-SECRET-TELEMETRY-TOKEN-2026`. |
| **Sink** | Unprotected internal endpoint using leaked secret | `src/index.js` | 149-160 | `app.get('/api/internal/telemetry'…)` | Only checks `x-telemetry-token` or `?token` header value. No IP restriction, no session check, no role gate. Returns `SELECT * FROM devices` — including `device_secret` column (e.g. `IOT-DEV-KEY-THERMO-1122`). |

### Preconditions

- User has valid credentials (registerable via `POST /api/auth/register` or by brute-forcing known seed users like `admin_iot`).
- Attacker knows to send `"TRIGGER-ERROR"` as a command to trigger the error path.

### Impact

- **Full device secret key exposure.** An attacker obtains the telemetry access key and uses it to hit `/api/internal/telemetry`, retrieving **all device secret keys** and internal system metadata.
- **Lateral movement to IoT devices.** With device secret keys, an attacker can authenticate as IoT devices on the backend network.
- **Information disclosure of debug configuration.** The `gateway_config` leak includes `debug_mode: true`, confirming debug readiness.

### Remediation

1. **Never include secrets in error responses.** The `catch` handler should return a generic error message without `stack` or `gateway_config`.
2. **Remove `debug_mode: true` and `gateway_config` from error payloads entirely.**
3. **Tighten `/api/internal/telemetry`** with IP-based allowlists, JWT-based admin auth, or both.

---

## Chained Vulnerability 2 — SSRF via Device Status Refresh + Telemetry Secret Exfiltration

### Severity: HIGH | Confidence: HIGH

### Mermaid Attack Graph

```mermaid
flowchart LR
    A["Authenticated User\nsrc/index.js:149"] -->|"POST /api/devices/refresh\nwith statusUrl parameter"| B["axios.get(statusUrl)\nsrc/index.js:151"]
    B -->|"Arbitrary URL fetch — no\nvalidation or allowlist"| C["SSRF: Attacker selects\ninternal URL\ne.g. http://localhost:8017/api/internal/telemetry"]
    C -->|"axios follows request\nto internal endpoint"| D["Internal endpoint runs\nwithout telemetry token\n(no auth on the axios call)"]
    D -->|"No token forwarded,\nattacker captures response"| E["Response data (device keys)\ncould be returned\nor proxied via res.json"]
    E -->|"Attacker can also target\nmetadata endpoints,\ncloud provider 169.254.169.254"| F["Impact: SSRF data\ncollection + internal\nservice enumeration")
```

### Chain Breakdown

| Link | Type | File | Lines | Symbol | Evidence |
|------|------|------|-------|--------|----------|
| **Source** | Unvalidated user-supplied URL | `src/index.js` | 149-158 | `app.post('/api/devices/refresh'…)` | `statusUrl` from `req.body` is passed directly to `axios.get()` with no allowlist, no protocol restriction, and no SSRF protections. |
| **Hop 1** | Internal endpoint accessible from app process | `src/index.js` | 149-160 | `app.get('/api/internal/telemetry'…)` | The internal telemetry endpoint listens on the same server (`localhost:8017`). An SSRF from this endpoint can reach it directly. However, the telemetry endpoint requires `x-telemetry-token` or `?token` — which the SSRF attacker **does not possess** unless Chain 1 is already executed. |
| **Hop 2** | Alternative SSRF targets without auth | `src/index.js` | 149-158 | `axios.get(statusUrl)` | Many cloud metadata services (AWS `169.254.169.254`, GCP metadata) and internal services often have no auth. The SSRF can reach these to collect cloud credentials, instance metadata, etc. |

### Preconditions

- Attacker is authenticated.
- Target environment runs on a cloud or internal network where metadata endpoints or internal services are reachable.

### Impact

- **SSRF to internal services** — arbitrary GET requests to internal URLs from the server process.
- **Cloud credential theft** — if deployed to cloud infrastructure, metadata endpoint access can expose IAM credentials.
- **Service enumeration and data exfiltration** — any service reachable from the app server is accessible via this SSRF.

### Remediation

1. **Implement an allowlist** of permitted `statusUrl` domains/paths.
2. **Reject private/reserved IP ranges** (10.x.x.x, 172.16–31.x.x, 192.168.x.x, 169.254.x.x, 127.x.x.x).
3. **Enforce HTTPS-only** for `statusUrl` to prevent MITM of device status checks.

---

## Chained Vulnerability 3 — No Role-Based Access Control on Device Commands + Full CRUD Exposure

### Severity: MEDIUM | Confidence: HIGH

### Mermaid Attack Graph

```mermaid
flowchart LR
    A["Registered User\n(regular CUSTOMER)\nsrc/index.js:108-116"] -->|"POST /api/auth/register\ncreates CUSTOMER role"| B["Session granted\nwith role: CUSTOMER\nsrc/index.js:124"]
    B -->|"requireAuth only checks\nsession existence\nsrc/index.js:75-80"| C["Unrestricted access to\nPOST /api/devices/command\nsrc/index.js:129"]
    C -->|"Any authenticated user\ncontrols any device"| D["No role check,\nno ownership check on deviceId"]
    D -->|"Attacker as CUSTOMER\ncommands admin-managed devices\nsrc/index.js:131-146"| E["Impact: Unauthorized device\ncontrol — potential\nIoT safety risk")
```

### Chain Breakdown

| Link | Type | File | Lines | Symbol | Evidence |
|------|------|------|-------|--------|----------|
| **Source** | Registration creates CUSTOMER role | `src/index.js` | 108-116 | `app.post('/api/auth/register'…)` | Anybody can register as `CUSTOMER` — no admin approval, no rate limiting. |
| **Hop 1** | `requireAuth` only checks session existence | `src/index.js` | 73-80 | `requireAuth(req, res, next)` | The guard checks `getSessionUser(req)` which reads the session cookie — it **never checks `user.role`**. |
| **Sink** | Device commands lack authorization | `src/index.js` | 129-146 | `app.post('/api/devices/command', requireAuth, …)` | The route accepts any authenticated user. No check on whether the user owns the device, has ADMIN role, or any other authorization. A `CUSTOMER` can issue commands to any device including admin-managed ones. |

### Impact

- **Unauthorized device control.** A regular user can send commands to any IoT device in the system.
- **Privilege escalation across role boundaries.** Despite having a `role` field on the `users` table, the application never enforces it.

### Remediation

1. **Add role-based checks** in `requireAuth` — e.g., `if (user.role !== 'ADMIN') return res.status(403)`.
2. **Add ownership checks** on device operations — verify the user's role or device assignments before allowing commands.
3. **Implement proper authorization middleware** that evaluates `req.user.role` against required roles per endpoint.

---

## Chained Vulnerability 4 — SQL Injection Potential + Session Token Weakness

### Severity: MEDIUM | Confidence: MEDIUM

### Mermaid Attack Graph

```mermaid
flowchart LR
    A["User-supplied username\nPOST /api/auth/login\nsrc/index.js:118"] -->|"Prepared statement\nwith parameterized query\nsrc/index.js:119"| B["SQL query:\nSELECT * FROM users WHERE username = ?"]
    B -->|"Safe: parameterized\n(no SQL injection on login) | C["However, /api/auth/register\nsrc/index.js:108-116"| D["INSERT with parameterized stmt"]
    D -->|"Safe: parameterized\n(no SQL injection) | E["SQLite :memory: store\nno persistence\nsrc/index.js:46"]
    E -->|"No session timeout,\nno token rotation\nsrc/index.js:70-80"| F["Weak session management:\nserver-side sessions in memory,\nno expiry, no invalidation"]
```

### Chain Breakdown

| Link | Type | File | Lines | Symbol | Evidence |
|------|------|------|-------|--------|----------|
| **Source** | User-controlled input in queries | `src/index.js` | 108-127 | Registration and login routes | Both use parameterized queries (`?` placeholders), which is good. |
| **Hop 1** | Session tokens are predictable | `src/index.js` | 125-127 | `cryptoRandomToken()` | Token generation uses `Math.random()` (not `crypto.randomBytes()`). Seeded PRNG can be predictable. |
| **Hop 2** | No session expiration or logout | `src/index.js` | 70-80, 123 | Session store and login | Sessions are stored in `sessions` object with no TTL, no `maxAge`, and no `/api/auth/logout` endpoint. |

### Impact

- **Session token brute-forcing.** The 32-character token from `Math.random()` has significantly less entropy than a proper CSPRNG-based token. An attacker could potentially brute-force or predict valid session tokens.
- **Persistent sessions.** Without expiry or logout, stolen tokens remain valid indefinitely until the server restarts (in-memory store).

### Remediation

1. Replace `cryptoRandomToken()` with `crypto.randomBytes(32).toString('hex')`.
2. Add `maxAge` / `expires` to session entries and implement periodic cleanup.
3. Add a `POST /api/auth/logout` endpoint that invalidates the session cookie and removes the session entry.

---

## Cross-Cutting Weaknesses Inventory

The following weaknesses were identified but do not independently form complete chains, or they are standalone issues:

| Weakness | File | Lines | Description |
|----------|------|-------|-------------|
| **CORS misconfiguration** | `src/index.js` | 14 | `cors({ origin: true, credentials: true })` — `origin: true` in some CORS library versions can reflect the `Origin` header, enabling any domain to make credentialed requests. Should use an explicit allowlist. |
| **Hardcoded debug credentials in source** | `src/index.js` | 144 | `telemetry_access_key: 'INTERNAL-SECRET-TELEMETRY-TOKEN-2026'` is hardcoded in the source code and in the error response. |
| **No rate limiting on auth endpoints** | `src/index.js` | 108, 118 | `/api/auth/register` and `/api/auth/login` have no rate limiting — enabling credential stuffing and mass account creation. |
| **Hardcoded seed credentials** | `src/index.js` | 54-56 | Users `alice_owner`/`alice123` and `admin_iot`/`adminSecureIoT2026!` are hardcoded in the database initialization. |
| **In-memory session store not suitable for production** | `src/index.js` | 70 | `const sessions = {}` — sessions are lost on process restart. Not scalable for production. |
| **SQLite in-memory database** | `src/index.js` | 46 | `new sqlite3.Database(':memory:')` — all data is lost on restart. |
| **Verbose error stack traces** | `src/index.js` | 141 | `stack: cmdErr.stack` leaks internal stack trace to the client. |
| **Missing Content-Type validation on JSON body** | `src/index.js` | 13 | `express.json()` parses all `Content-Type: application/json` without further validation. |
| **No input sanitization on device names/secrets** | `src/index.js` | 50-57 | Seed data uses hardcoded secrets; no input validation on registered device secrets. |

---

## Unknowns and Areas Not Reviewed

| Area | Reason |
|------|--------|
| **Runtime environment** | Dockerfile provides minimal info; cannot determine if network namespaces, capabilities, or resource limits are configured. |
| **Database schema completeness** | Only `users` and `devices` tables are visible; other tables or migrations may exist outside reviewed files. |
| **TLS/HTTPS configuration** | Not visible in source; cannot assess transport layer security. |
| **Infrastructure / deployment** | No Kubernetes manifests, CI/CD pipelines, or infrastructure-as-code reviewed. |
| **Logging / monitoring** | No log aggregation or alerting mechanisms reviewed. |
| **Dependency vulnerability scan** | `node_modules` contains many dependencies but static audit focused on application code; `npm audit` not performed. |
| **Mobile / frontend clients** | This is a backend-only review; no frontend code or mobile SDKs analyzed. |

---

## Recommended Tests to Add

1. **Unit test:** Verify `cryptoRandomToken()` produces sufficiently random output (statistical tests).
2. **Integration test:** Confirm `/api/internal/telemetry` rejects requests without the correct telemetry token.
3. **Integration test:** Verify `/api/devices/refresh` rejects private IPs, `localhost`, and `file://` URIs.
4. **Integration test:** Confirm that a `CUSTOMER`-role user cannot access admin-only device management endpoints.
5. **Integration test:** Validate that `/api/devices/command` error responses do not include stack traces or internal config.
6. **Integration test:** Ensure CORS only allows explicitly configured origins.

---

## Remediation Priority

| Priority | Action | Effort | Impact |
|----------|--------|--------|--------|
| **P0 (Immediate)** | Remove `gateway_config` and `stack` from error responses (`/api/devices/command` catch block) | Low | Prevents HIGH-severity chain #1 |
| **P0 (Immediate)** | Replace `Math.random()` with `crypto.randomBytes()` for session tokens | Low | Prevents session token prediction |
| **P1 (Short-term)** | Add allowlist / IP blocking for `/api/devices/refresh` SSRF input | Medium | Prevents HIGH-severity chain #2 |
| **P1 (Short-term)** | Remove hardcoded secrets from source code | Low | Reduces credential exposure risk |
| **P2 (Medium-term)** | Implement role-based authorization checks | Medium | Prevents MEDIUM-severity chain #3 |
| **P2 (Medium-term)** | Add session expiration and logout endpoint | Low | Strengthens session management |
| **P3 (Long-term)** | Add rate limiting on all endpoints | Medium | Prevents abuse and brute-force |
| **P3 (Long-term)** | Switch to Redis for session store and persistent database | High | Improves production readiness |

---

*Report generated by CodeGopher — Static-Only Chained Vulnerability Audit*  
*No live testing, dynamic scanning, or exploit execution was performed.*
