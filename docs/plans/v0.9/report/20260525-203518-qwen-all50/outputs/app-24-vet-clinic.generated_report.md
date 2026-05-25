# Chained Vulnerability Audit Report

**Project**: Veterinary Clinic Management API (FastAPI)
**Date**: 2026-05-25
**Scope**: Full static review of `app.py`, `reference_guards.py`, `requirements.txt`, `Dockerfile`
**Methodology**: Chained vulnerability static audit — source-only analysis, no live probes or dynamic testing

---

## Summary Dashboard

| Metric | Value |
|---|---|
| **Total chains identified** | 3 |
| **Maximum severity** | **Critical** |
| **High severity chains** | 2 |
| **Medium severity chains** | 0 |
| **Cross-cutting weaknesses** | 4 |
| **Confidence level** | High (every link provable from source) |

### Reviewed Areas
- Authentication & authorization logic (JWT handling, role checks)
- Database access patterns (SQLite queries, ORM usage)
- Input validation & sanitization
- Audit logging coverage
- Response security (error details, debug output)
- Container configuration

### Areas Not Reviewed
- Runtime dependency vulnerability scan (no live CVE checks)
- Network security (TLS, CORS headers, security headers)
- Deployment configuration (no env-specific configs found)
- Penetration testing or dynamic analysis

---

## Safety Note

This review is **static-only**. No live HTTP probes, SQL injection payloads, credential attacks, fuzzers, or exploit scripts were executed. All findings are derived from source code analysis alone. Remediation recommendations are high-level and do not contain operational abuse instructions.

---

## Chain 1 — JWT Forgery → Privilege Escalation → Full Application Access

**Severity**: High | **Confidence**: High

### Attack Graph

```mermaid
flowchart LR
    A["Hardcoded JWT Secret\n(app.py: JWT_SECRET = \"secret123\")"] --> B["Forge arbitrary JWT tokens\nwith any role: VET, ADMIN"]
    B --> C["Bypass role-based access\non all endpoints"]
    C --> D["Read: /api/pets/search\n/api/pets\n/api/appointments\n/api/audit/logs"]
    C --> E["Write: /api/prescriptions/{id}/update\n/api/appointments"]
    D --> F["Full data exfiltration +\nintegrity compromise"]
    E --> F
```

### Detailed Breakdown

| Link | File | Lines | Evidence |
|---|---|---|---|
| **Source** | `app.py` | JWT_SECRET assignment | `JWT_SECRET = "secret123"` — hardcoded, trivially guessable string used to sign all JWTs |
| **Hop 1** | `app.py` | `generate_token()` | Token payload contains `{"role": role}` signed with the known secret using HS256 |
| **Hop 2** | `app.py` | `verify_token()` | `jwt.decode(token, JWT_SECRET, algorithms=["HS256"])` — no key rotation, no audience/issuer validation |
| **Sink** | `app.py` | Role checks | Every endpoint checks `token_data.get('role') in ('VET', 'ADMIN')` — no server-side session or user lookup beyond the JWT payload |

### Preconditions & Assumptions
- Attacker can discover the JWT secret (hardcoded in source, trivially visible to anyone with code access or via source-code exposure)
- JWT secret is used server-wide with no per-user or per-environment rotation

### Impact
An attacker forges an `ADMIN` JWT and gains full access to:
- `GET /api/audit/logs` — read all audit events
- `GET /api/pets/search` — search all pet records (with SQL injection, see Chain 2)
- `POST /api/pets` — create arbitrary pet records linked to any owner
- `POST /api/prescriptions/{id}/update` — modify any prescription

### Remediation
1. Replace hardcoded `JWT_SECRET` with an environment variable loaded via `os.environ` or a secrets manager.
2. Add `aud` (audience) and `iss` (issuer) claims to JWT payload and validate them in `verify_token()`.
3. Consider binding JWT tokens to a user identity table lookup on sensitive endpoints rather than trusting the role claim alone.

---

## Chain 2 — SQL Injection → Full Database Exfiltration

**Severity**: High | **Confidence**: High

### Attack Graph

```mermaid
flowchart LR
    A["User-controlled param\nq in GET /api/pets/search"] --> B["String interpolation:\nf\"SELECT * FROM pets WHERE name LIKE '%{q}%'\"\n(app.py: search_pets)"]
    B --> C["SQL Injection via UNION\nor subquery-based extraction"]
    C --> D["Debug response field:\n\"debug_query\": query\nexposes query to client"]
    D --> E["Attribute: Error details\nleaked on SQLite failure:\n\"detail\": str(e)"]
    E --> F["Full table access:\nusers, prescriptions,\nappointments via SQLite"]
    F --> G["Database exfiltration:\nusername/password hashes,\ncontrolled substance data,\nowner IDs"]
```

### Detailed Breakdown

| Link | File | Lines | Evidence |
|---|---|---|---|
| **Source** | `app.py` | `search_pets()` parameter | `q: str` is a raw query parameter with no sanitization |
| **Hop 1** | `app.py` | `search_pets()` SQL construction | `query = f"SELECT * FROM pets WHERE name LIKE '%{q}%"'` — f-string interpolation of user input into SQL |
| **Hop 2** | `app.py` | `search_pets()` response | `"debug_query": query` returns the constructed SQL to the client, confirming injection point and revealing table names |
| **Hop 3** | `app.py` | `search_pets()` error handler | `except Exception as e: raise HTTPException(status_code=400, detail=str(e))` — database error messages are returned verbatim |
| **Sink** | `app.py` | `init_db()` schema | Tables `users`, `pets`, `prescriptions`, `appointments` with columns including `password_hash`, `drug_name`, controlled substance data |

### Preconditions & Assumptions
- Attacker needs a valid JWT token (any role works for `/api/pets/search` as long as VET or ADMIN — or can forge one per Chain 1)
- SQLite supports `UNION`-based extraction and `sqlite_schema` table introspection
- No WAF or input filtering is deployed (no evidence of such in the codebase)

### Impact
An attacker can:
- Extract all user credentials (`username`, `password_hash`) from the `users` table
- Extract all prescription data including controlled substances (Phenobarbital)
- Discover owner IDs and full pet records
- Use union-based injection to dump the entire `appointments` table

### Remediation
1. Replace f-string SQL with parameterized queries:
   ```python
   cursor.execute("SELECT * FROM pets WHERE name LIKE ?", (f"%{q}%",))
   ```
2. Remove `"debug_query"` from the response in production.
3. Remove or sanitize the `except` block to return generic error messages.

---

## Chain 3 — JWT Forgery + SQL Injection + Missing Audit Logging → Untraceable Prescription Tampering

**Severity**: Critical | **Confidence**: High

### Attack Graph

```mermaid
flowchart LR
    A["Hardcoded JWT Secret\n(app.py: JWT_SECRET = \"secret123\")"] --> B["Forge VET/ADMIN JWT token"]
    B --> C["Access /api/prescriptions/{id}/update\nwith forged token"]
    C --> D["SQL Injection in\n/api/pets/search\n(to find all prescription IDs)"]
    D --> E["Enumerate all prescription IDs\nvia UNION SELECT on prescriptions table"]
    E --> F["Modify any prescription\n(drug_name, dosage)"]
    F --> G["NO audit log written:\nlog_audit_event() never called\nin update_prescription()"]
    G --> H["Untraceable controlled\nsubstance modifications\n— compliance violation"]
```

### Detailed Breakdown

| Link | File | Lines | Evidence |
|---|---|---|---|
| **Source** | `app.py` | JWT_SECRET | `"secret123"` — forge VET role token |
| **Hop 1** | `app.py` | `verify_token()` | No server-side user validation — role claim is trusted verbatim |
| **Hop 2** | `app.py` | `update_prescription()` | Role check: `token_data.get('role') not in ('VET', 'ADMIN')` — bypassable via forged token |
| **Hop 3** | `app.py` | `search_pets()` | SQL injection to enumerate prescription IDs via `UNION SELECT id FROM prescriptions` |
| **Hop 4** | `app.py` | `update_prescription()` | SQL UPDATE is parameterized (safe), but **`log_audit_event()` is never called** — confirmed by code inspection. In-code comment explicitly notes: "changes of controlled substances occur with zero audit logging" |
| **Sink** | N/A | Business impact | Unauthorized modifications to prescriptions for controlled substances (e.g., Phenobarbital) with zero audit trail |

### Preconditions & Assumptions
- Attacker has identified the hardcoded JWT secret (source code access or leak)
- Attacker uses SQL injection to enumerate prescription IDs
- Clinic relies on audit logs for compliance and accountability (business assumption confirmed by the `audit_logs` list and `/api/audit/logs` endpoint)

### Impact
- **Confidentiality**: Full prescription data accessible
- **Integrity**: Controlled substance prescriptions can be altered without detection
- **Compliance**: HIPAA / pharmacy regulation violations — no audit trail for controlled substance changes
- **Legal/Liability**: Clinic cannot prove who modified prescriptions or what was modified

### Remediation
1. **Audit logging**: Call `log_audit_event()` at the start of `update_prescription()` with `action="UPDATE_PRESCRIPTION"`, capturing old and new values.
2. **Persist audit logs**: Replace in-memory `audit_logs` list with persistent storage (database table) so logs survive restarts.
3. **Chain with Chain 1 remediation**: Fix the JWT secret to prevent token forgery.
4. **Chain with Chain 2 remediation**: Fix SQL injection to prevent prescription ID enumeration.
5. **Add authorization for controlled substances**: Require additional approval or separate audit flags for prescription changes involving controlled substances.

---

## Cross-Cutting Weaknesses

### WC-1: Verbose Error Messages
- **Location**: `app.py`, `search_pets()` error handler
- **Code**: `raise HTTPException(status_code=400, detail=str(e))`
- **Risk**: Internal SQLite errors (table names, column types, constraint violations) leak to attackers, aiding SQL injection crafting

### WC-2: No CSRF Protection on POST Endpoints
- **Location**: `app.py` — `POST /api/pets`, `POST /api/prescriptions/{id}/update`, `POST /api/appointments`
- **Risk**: If a user is authenticated, a malicious website could craft cross-origin POST requests to modify data. This is mitigated somewhat by the JWT cookie/token requirement, but if tokens are stored in `localStorage` or accessible to scripts, CSRF-like attacks via iframe/embedding may be feasible. FastAPI does not enable CSRF protection by default.

### WC-3: No Rate Limiting on Authentication
- **Location**: `app.py`, `login()` endpoint
- **Risk**: No throttling on `POST /api/auth/login` — enables brute-force password attacks against user accounts. Passwords are bcrypt-hashed (good), but passwords may be weak (seed data suggests simple passwords like `john_pass`, `vet_pass`, `admin_pass`).

### WC-4: Owner ID Not Validated Against Token Identity
- **Location**: `app.py`, `create_pet()`
- **Code**: `req.owner_id` comes from the request body, validated by Pydantic as `int` only
- **Risk**: A VET user can create a pet record linked to any `owner_id`, not just their own. This could enable cross-owner data pollution. The `reference_guards.py` module defines a `same_owner()` helper function that is never used.

---

## Unknowns & Not-Reviewed Areas

| Area | Reason | Recommendation |
|---|---|---|
| TLS/HTTPS configuration | No configuration in Dockerfile or app.py | Verify production deployment uses HTTPS |
| CORS policy | No `CORSMiddleware` in app.py | May be intentionally restrictive; verify intended behavior |
| Input length limits | Pydantic models validate ranges but not string length | Add max_length to text fields (drug_name, dosage, reason, etc.) |
| File uploads | None detected | N/A |
| Third-party integrations | None detected | N/A |
| Dependency CVEs | Static-only scope | Run `pip-audit` or equivalent on `requirements.txt` |

---

## Remediation Priority Summary

| Priority | Issue | Chains Broken |
|---|---|---|
| **P0 (Immediate)** | Fix hardcoded JWT secret | Chain 1, Chain 3 |
| **P0 (Immediate)** | Parameterize SQL query in `search_pets()` | Chain 2, Chain 3 |
| **P1 (Short-term)** | Add audit logging to `update_prescription()` | Chain 3 |
| **P1 (Short-term)** | Remove debug query from response | Chain 2 |
| **P2 (Medium-term)** | Add rate limiting to login endpoint | WC-3 |
| **P2 (Medium-term)** | Validate owner_id against authenticated user | WC-4 |
| **P3 (Long-term)** | Add CSRF protection | WC-2 |
| **P3 (Long-term)** | Persist audit logs to database | Chain 3 |
| **P3 (Long-term)** | Sanitize error messages | WC-1 |

---

## Conclusion

Three chained vulnerability paths were identified, with the most critical chain combining **JWT token forgery**, **SQL injection**, and **missing audit logging** to enable untraceable prescription tampering. The root causes are a hardcoded JWT secret, unsanitized SQL query construction, and absent audit instrumentation for sensitive operations. Remediation of the P0 items alone breaks all three chains and eliminates all identified chains.
