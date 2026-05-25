# Chained Vulnerability Audit Report

**Application**: Veterinary Clinic Management System (FastAPI)
**Audit Date**: 2026-05-25
**Auditor**: CodeGopher (Static-Only Chained Vulnerability Audit)
**Scope**: `app.py`, `requirements.txt`, `Dockerfile` in project root

---

## Executive Summary

| Metric | Value |
|---|---|
| **Total chains identified** | 3 |
| **Maximum severity** | HIGH |
| **Confidence levels** | 2 High, 1 Medium |
| **Root causes** | Hardcoded secrets, SQL injection, missing authorization, absent audit logging |
| **Easiest remediation** | Use environment-variable-based JWT secret (breaks 2 chains) |

---

## Methodology & Safety Note

This audit is **static-only**: it inspects source code, configuration, dependency manifests, and Dockerfile. No live HTTP probes, dynamic scanners, SQL injection payloads, or external network tests were performed. No exploit scripts or operational abuse instructions are included.

---

## Reviewed Areas

| Area | Files | Notes |
|---|---|---|
| Authentication & Authorization | `app.py` (JWT, role checks, `verify_token`) | Role enforcement present but bypassable via forged tokens |
| Database layer | `app.py` (SQLite, parameterized vs. f-string queries) | Mixed use of safe `?`-parameterized queries and unsafe f-string interpolation |
| API endpoints | `app.py` (all `@app.*` routes) | 8 endpoints; varied authorization and input handling |
| Audit logging | `app.py` (`log_audit_event`, selective use) | Only appointment scheduling logs; prescription updates and many actions are silent |
| Dependencies | `requirements.txt` | FastAPI 0.111.0, PyJWT 2.8.0, bcrypt 4.1.3 |
| Container | `Dockerfile` | Minimal attack surface; runs as root inside container |

---

## Areas Not Reviewed / Unknowns

| Area | Reason |
|---|---|
| Runtime behavior | Cannot verify that in-memory DB actually persists correctly across restarts (it's `:memory:`) |
| Production deployment | No `SECRET_KEY` env var configured; this code likely intended for demo only |
| TLS/HTTPS | Not configured; would be required in production |
| CORS policy | No CORS middleware configured; defaults may be permissive |
| Rate limiting | No rate limiting on `/api/auth/login` — brute-force feasible |
| Input length limits | `name`, `species`, `reason` fields have no max-length validation |
| Prescription ownership checks | No validation that the vet updating a prescription actually owns it or is assigned to it |
| JWT expiration enforcement | Expiration is set but default PyJWT behavior does not reject expired tokens without explicit check (PyJWT 2.8.0 should do this, but worth verifying) |

---

## Chain 1: JWT Forge → SQL Injection → Database Exfiltration

**Severity**: HIGH
**Confidence**: HIGH

### Mermaid Attack Graph

```mermaid
flowchart LR
    A["No-Auth User"] -->|Forge JWT with hardcoded secret| B["Forged VET Token"]
    B -->|Pass verify_token() check| C["/api/pets/search endpoint"]
    C -->|Passes role check 'VET'| D["SQL Injection in f-string query"]
    D -->|Execute arbitrary SQL| E["EXFILTRATE: users, passwords, prescriptions, all data"]
```

### Detailed Breakdown

| Link | File | Lines | Symbol/Reference | Evidence |
|---|---|---|---|---|
| **Source**: Hardcoded JWT secret | `app.py` | 14 | `JWT_SECRET = "secret123"` | Literal string "secret123" is used for HS256 token signing |
| **Hop 1**: Forge JWT as VET | `app.py` | 62-69 | `generate_token()` | Any attacker with known secret can construct arbitrary payloads with `"role": "VET"` |
| **Hop 2**: Bypass role check | `app.py` | 100-101 | `verify_token()` + `Depends` | `verify_token` decodes with known secret and returns payload; only checks `role in ('VET', 'ADMIN')` |
| **Sink**: SQL injection | `app.py` | 128 | `query = f"SELECT * FROM pets WHERE name LIKE '%{q}%'"` | User-controlled `q` parameter interpolated directly into SQL via f-string; passed to `cursor.execute(query)` |
| **Sink**: Debug query leak | `app.py` | 132 | `"debug_query": query` | Raw SQL query (including injected payload) returned in response JSON |

### Preconditions & Assumptions

- The attacker knows or guesses the hardcoded secret (trivial given it's "secret123").
- PyJWT `decode` with `algorithms=["HS256"]` does not verify the key is secret (it's hardcoded, so verification succeeds for forged tokens).
- SQLite supports all standard SQL injection techniques (`UNION SELECT`, `;', 'DROP TABLE...`, etc.).

### Impact

- **Full database read**: Extract all users, password hashes, pet records, prescriptions, appointments.
- **Data manipulation**: INSERT/UPDATE/DELETE via stacked queries (if `fetchall` style call allows it — `sqlite3` in Python may block by default, but schema extraction via `UNION SELECT` is trivial).
- **Schema discovery**: Query `sqlite_master` for table/column info.

### Remediation (easiest link to break first)

1. **Primary (breaks both Source and Hop 1)**: Store JWT secret in an environment variable:
   ```python
   JWT_SECRET = os.environ.get("JWT_SECRET", "CHANGE-ME-TO-STRONG-RANDOM-KEY")
   ```
   Use a cryptographically random 256+ bit key.

2. **Defense-in-depth (breaks Sink)**: Replace f-string SQL with parameterized queries:
   ```python
   cursor.execute("SELECT * FROM pets WHERE name LIKE ?", (f"%{q}%",))
   ```

---

## Chain 2: JWT Forge → Admin Privilege Escalation → Zero-Audit Prescription Tampering

**Severity**: HIGH
**Confidence**: HIGH

### Mermaid Attack Graph

```mermaid
flowchart LR
    A["No-Auth User"] -->|Forge JWT as ADMIN| B["Forged ADMIN Token"]
    B -->|Pass verify_token()| C["/api/prescriptions/{id}/update"]
    C -->|Role check passes 'ADMIN'| D["UPDATE prescriptions (no audit log)"]
    D -->|Changes drug_name/dosage| E["Tampered prescriptions — no audit trail"]
    
    B -->|Also accesses| F["/api/audit/logs"]
    F -->|Admin-only, but attacker has forged token| G["View all audit logs (blind)"]
```

### Detailed Breakdown

| Link | File | Lines | Symbol/Reference | Evidence |
|---|---|---|---|---|
| **Source**: Hardcoded JWT secret | `app.py` | 14 | `JWT_SECRET = "secret123"` | Same as Chain 1 |
| **Hop 1**: Forge JWT as ADMIN | `app.py` | 62-69 | `generate_token()` | Set `"role": "ADMIN"` in payload |
| **Hop 2**: Admin-only route bypass | `app.py` | 178-180 | `view_audit_logs` | `if token_data.get('role') != 'ADMIN': raise 403` — bypassable with forged token |
| **Sink**: No audit on prescription update | `app.py` | 144-160 | `update_prescription()` | No call to `log_audit_event()`; prescription changes are silent |
| **Sink**: Blind spot in audit | `app.py` | 182 | `view_audit_logs` returns all logs | Attacker can read logs to confirm their tampering is not logged |

### Preconditions & Assumptions

- Forge capability is the same as Chain 1.
- Prescription updates are not validated against prescription ownership (the vet may not be the original prescriber).
- In-memory SQLite means data is lost on restart, but tampering is still effective during the session.

### Impact

- **Unauthorized prescription changes**: Alter drug names and dosages without detection.
- **Regulatory/compliance risk**: Prescriptions (especially controlled substances) must be auditable. Zero logging means the clinic cannot detect or investigate tampering.
- **Insider threat enablement**: If deployed with a real secret, social engineering or token theft could achieve the same result.

### Remediation

1. **Break Hop 1**: Fix JWT secret (env var, strong random key) — same as Chain 1.
2. **Break Sink**: Add audit logging to `update_prescription`:
   ```python
   log_audit_event(
       action="UPDATE_PRESCRIPTION",
       user=token_data.get("sub"),
       details=f"Prescription {prescription_id} updated: drug={req.drug_name}, dosage={req.dosage}"
   )
   ```
3. **Defense-in-depth**: Add ownership/assignment validation — ensure the requesting vet is associated with the prescription's pet.

---

## Chain 3: JWT Forge → Unauthorized Pet Owner Assignment → Data Integrity Violation

**Severity**: MEDIUM
**Confidence**: MEDIUM

### Mermaid Attack Graph

```mermaid
flowchart LR
    A["No-Auth User"] -->|Forge JWT as VET| B["Forged VET Token"]
    B -->|Pass verify_token()| C["POST /api/pets"]
    C -->|Accepts owner_id from request body| D["Assign pet to ANY owner_id"]
    D -->|No ownership validation| E["Pet records linked to arbitrary users"]
```

### Detailed Breakdown

| Link | File | Lines | Symbol/Reference | Evidence |
|---|---|---|---|---|
| **Source**: Hardcoded JWT secret | `app.py` | 14 | `JWT_SECRET = "secret123"` | Same root cause |
| **Hop 1**: Forge VET token | `app.py` | 62-69 | `generate_token()` | Same forge path |
| **Hop 2**: Authorization pass | `app.py` | 117 | `if token_data.get('role') not in ('VET', 'ADMIN')` | Role check passes |
| **Sink**: No owner validation | `app.py` | 120-123 | `cursor.execute(... (req.owner_id, ...)` | `owner_id` is taken directly from the request body with no check that it belongs to the authenticated user |

### Preconditions & Assumptions

- JWT forge capability exists (depends on whether a real secret is used in production).
- The `PetCreateRequest` model accepts `owner_id` from the client.
- In a real system, customers should only create pets for themselves, and vets should only create pets for known clients.

### Impact

- **Data integrity**: Pets can be assigned to arbitrary user IDs, corrupting the ownership model.
- **Privacy**: Vets could link pet records to wrong owners, causing confusion and potential HIPAA-like violations (animal health data tied to wrong person).
- **Further exploitation**: If an admin later queries pet ownership for billing or notifications, incorrect data propagates.

### Remediation

1. **Break Hop 1**: Fix JWT secret.
2. **Break Sink**: Derive `owner_id` from the authenticated token instead of the request body:
   ```python
   # In create_pet, replace req.owner_id with token_data.get('user_id')
   cursor.execute(
       "INSERT INTO pets (owner_id, name, species, age, weight) VALUES (?, ?, ?, ?, ?)",
       (token_data.get('user_id'), req.name, req.species, req.age, req.weight)
   )
   ```

---

## Cross-Cutting Weaknesses (Not Complete Chains)

These are security-relevant issues that, on their own, may not form a full attack chain but represent notable weaknesses:

| Weakness | File | Lines | Impact |
|---|---|---|---|
| **No CSRF protection** | `app.py` | All POST endpoints | Browsers sending authenticated cookies could trigger state-changing requests from malicious sites |
| **No rate limiting on login** | `app.py` | 104-108 | Brute-force password attacks are feasible against `/api/auth/login` |
| **Verbose error messages** | `app.py` | 133 | `detail=str(e)` exposes database errors to clients |
| **No input length limits** | `app.py` | 84-89, 93-97 | `name`, `species`, `reason` accept arbitrarily long strings (potential DoS) |
| **In-memory SQLite in Docker** | `Dockerfile` + `app.py` | 18-19 | Data lost on every restart; no persistence |
| **Runs as root in container** | `Dockerfile` | 1 | Non-root user should be used |
| **No HTTPS/TLS** | `Dockerfile` + `app.py` | 172 | `host='0.0.0.0', port=8094` — no SSL termination |

---

## Testing Recommendations

Tests that should be added to verify remediations:

1. **JWT secret randomness**: Test that the application reads `JWT_SECRET` from an environment variable and rejects tokens signed with a known default.
2. **SQL injection unit test**: Send `' OR '1'='1` to `/api/pets/search` and verify it is parameterized (returns no results or an error, not all rows).
3. **Authorization unit test**: Verify that a `CUSTOMER` role cannot access `/api/pets/search`.
4. **Audit logging integration test**: Confirm that `POST /api/prescriptions/{id}/update` creates an audit log entry.
5. **Owner validation test**: Verify that `POST /api/pets` assigns the pet to the authenticated user's ID, not a client-supplied `owner_id`.
6. **Rate limiting test**: Verify that >10 failed login attempts in 1 minute returns 429.

---

## Remediation Priority Summary

| Priority | Action | Chains Broken |
|---|---|---|
| **P0** | Replace hardcoded `JWT_SECRET` with env-var-based strong random key | Chains 1, 2, 3 |
| **P0** | Parameterize SQL query in `/api/pets/search` | Chain 1 |
| **P1** | Add audit logging to `/api/prescriptions/{id}/update` | Chain 2 |
| **P1** | Derive `owner_id` from JWT token in `/api/pets` | Chain 3 |
| **P2** | Add rate limiting to `/api/auth/login` | New attack prevention |
| **P2** | Remove `debug_query` from API responses | Chain 1 defense-in-depth |
| **P3** | Add CSRF protection to POST endpoints | General hardening |
| **P3** | Add input length validation | General hardening |
| **P3** | Run container as non-root user | Infrastructure hardening |

---

*Report generated by CodeGopher. Static-only audit. No live systems were probed.*
