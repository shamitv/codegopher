# Chained Vulnerability Static Audit Report

**Project:** Smart Home Device Manager (`app.py`)  
**Date:** 2026-05-24  
**Auditor:** CodeGopher — Chained Vulnerability Static Audit  
**Scope:** `app.py`, `Dockerfile`, `requirements.txt`  
**Approach:** Static source-code analysis only. No live probes, fuzzers, or network tests.

---

## 1. Summary Dashboard

| Metric | Value |
|---|---|
| **Total chains identified** | **3** |
| **Critical-severity chains** | **2** |
| **High-severity chains** | **1** |
| **Cross-cutting weaknesses** | **5** |
| **Areas reviewed** | Routes, auth, DB, SSRF, firmware, config, Docker |
| **Areas not reviewed** | External dependencies (FastAPI, requests internals), runtime config (TLS, CORS, CSP) |

### Maximum Severity: **CRITICAL**

Two independent chains begin with an **unauthenticated** entry point and lead to full physical device control or internal network data exfiltration.

---

## 2. Methodology & Safety Note

- **Phase 1 — Attack Surface Mapping:** Enumerated all public routes, parameter sources (query params, headers, cookies, JSON body), and internal helpers.
- **Phase 2 — Weakness Inventory:** Catalogued individually modest weaknesses including missing auth, SSRF inputs, hardcoded seeds, and absent integrity checks.
- **Phase 3 — Attack Graph Synthesis:** Connected entry points → intermediate weaknesses → critical sinks using static control-flow and data-flow evidence from `app.py`.
- **Phase 4 — Impact Assessment:** Each chain is rated by impact, reachability, confidence, and the easiest remediation link to break.

**Static-Only Boundary:** This review examines source code, configuration files, and schemas. No HTTP probes, SQLi payloads, or dynamic scanners were executed. No executable exploit payloads are included.

---

## 3. Chain #1 — Unauthenticated Device Token Theft → Physical Device Control

### Severity: CRITICAL | Confidence: High

### Attack Graph

```mermaid
flowchart LR
    A[Unauthenticated Attacker] -->|GET /api/debug/devices| B[Debug Endpoint: No Auth]
    B -->|Returns api_token for all devices| C[Device API Tokens Exposed]
    C -->|POST /api/devices/{id}/command with X-Device-Token| D[Arbitrary Command Dispatch]
    D -->|Physical device executes command| E[Smart Lock opens, Garage opens, Thermostat changed]
```

### Detailed Breakdown

| Link | Location | Evidence |
|---|---|---|
| **Entry / Source** | `app.py`, lines 79-83 | `def debug_devices():` — no `Depends(get_current_user)`, no auth decorator, returns all device rows including `api_token` field. |
| **Hop 1 — Data leak** | `app.py`, line 82 | `{"devices": [dict(r) for r in rows]}` — serializes every column from `devices` table, including `api_token` values `tok_thermostat_9982x`, `tok_lock_1102z`, `tok_garage_4431a`. |
| **Hop 2 — Token usage** | `app.py`, lines 117-130 | `send_device_command()` validates `X-Device-Token` header against the `api_token` column. Any token found in the DB grants command dispatch for that device. |
| **Sink — Impact** | `app.py`, lines 117-130 | Command `'ON'`/''OFF'' sent to physical smart-home actuators (locks, garage door openers, thermostats). |

### Preconditions & Assumptions

- The application is running and reachable on port 8097.
- No WAF or reverse-proxy layer blocks the `/api/debug/` path.
- Device commands dispatched cause real-world physical actions (assumed from the domain context).

### Impact

An **unauthenticated** external attacker can enumerate every device API token and issue arbitrary commands to every connected smart-home device. This includes unlocking front doors and opening garage doors — a physical-security impact.

### Remediation (Easiest Link to Break)

- **Add authentication** to `debug_devices()`: require `Depends(get_current_user)` or higher admin role. Better: remove the debug endpoint entirely from production.

---

## 4. Chain #2 — Authenticated SSRF → Internal Network Data Exfiltration

### Severity: CRITICAL | Confidence: High

### Attack Graph

```mermaid
flowchart LR
    A[Authenticated Attacker] -->|GET /api/devices/sensor-data?url=<evil>| B[SSRF: requests.get(url)]
    B -->|Fetches internal service / cloud metadata| C[Internal API Data / Cloud Credentials]
    C -->|Returns content in response| D[Data Exfiltration to Attacker]
```

### Detailed Breakdown

| Link | Location | Evidence |
|---|---|---|
| **Entry / Source** | `app.py`, line 86 | `def fetch_sensor_data(url: str, user: dict = Depends(get_current_user)):` — `url` is a raw query parameter. |
| **Hop 1 — No validation** | `app.py`, line 88 | `requests.get(url, timeout=5)` — the URL is passed directly with no scheme/hostname/port whitelist, no redirect following control, no DNS-rebind mitigation. |
| **Sink — Impact** | `app.py`, line 89 | `{"success": True, "content": resp.text[:2000]}` — arbitrary HTTP response body (up to 2000 chars) is returned to the attacker. |

### Preconditions & Assumptions

- Attacker has valid credentials (could be obtained via brute-force on `/api/auth/login` due to missing rate limiting on login, or from the seed credentials in source code).
- The application runs in a network with accessible internal services (e.g., Docker network, cloud instance metadata at `169.254.169.254`).
- DNS resolution from the app host can reach internal hostnames.

### Impact

An authenticated attacker can read data from any reachable host on the internal network, including cloud provider instance metadata endpoints (which expose IAM credentials, container registry keys, etc.). This can lead to lateral movement and further compromise.

### Remediation (Easiest Link to Break)

- **Whitelist allowed URLs** for `fetch_sensor_data()`: only permit `https://` scheme and a set of known external sensor API domains. Reject `127.0.0.0/8`, `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, and `169.254.0.0/16` ranges at the application level.

---

## 5. Chain #3 — Authenticated SSRF + No Integrity Verification → Persistent Device Compromise

### Severity: HIGH | Confidence: High

### Attack Graph

```mermaid
flowchart LR
    A[Authenticated Attacker] -->|POST /api/devices/{id}/firmware/update| B[SSRF: requests.get(firmware_url)]
    B -->|Fetches arbitrary firmware binary| C[Raw binary stored/used directly]
    C -->|firmware_version updated via unsanitized length| D[Device updated to attacker-controlled firmware]
    D -->|Persistent backdoor on physical device| E[Long-term unauthorized access]
```

### Detailed Breakdown

| Link | Location | Evidence |
|---|---|---|
| **Entry / Source** | `app.py`, line 98 | `def update_firmware(device_id: int, req: FirmwareUpdateRequest, ...)` — `req.firmware_url` is taken from the JSON body. |
| **Hop 1 — SSRF** | `app.py`, line 103 | `requests.get(req.firmware_url, timeout=10)` — same SSRF weakness as Chain #2. |
| **Hop 2 — No integrity check** | `app.py`, lines 105-112 | Response binary is used directly. No SHA-256 hash comparison, no code-signature verification, no origin/HOST header check against a trusted CDN. Version is derived from `binary_size % 100` — purely cosmetic. |
| **Sink — Impact** | `app.py`, line 110 | `UPDATE devices SET firmware_version = ?` — the database reflects the attacker-chosen (actually size-derived) version; the binary itself is assumed pushed to the physical device. |

### Preconditions & Assumptions

- Attacker has valid credentials (same path as Chain #2).
- The physical device actually installs the fetched binary (assumed from the domain model; the DB record is updated regardless).
- The 10-second timeout is sufficient to fetch a malicious payload.

### Impact

An authenticated attacker can deliver a crafted binary as firmware to any device in the inventory. Without signature or hash verification, the system cannot detect tampered or malicious firmware. The result is persistent, hard-to-detect compromise of smart-home hardware.

### Remediation (Easiest Link to Break)

- **Enforce firmware integrity:** Require the request to include a signed manifest (e.g., HMAC-SHA256 signed by a server-held key). Reject firmware URLs not hosted on a whitelisted domain. Compute and verify a hash of the fetched binary before applying.

---

## 6. Cross-Cutting Weaknesses (Not in Complete Chains)

| Weakness | Location | Evidence |
|---|---|---|
| **Hardcoded seeded passwords** | `app.py`, lines 42-43 | `('owner_alice', bcrypt.hashpw(b'alice_home_2026', ...), 'USER')` and `('admin', bcrypt.hashpw(b'admin_home_2026', ...), 'ADMIN')`. Plaintext passwords in source; an attacker with code access knows both credentials. |
| **No rate limiting on login** | `app.py`, line 56 | `/api/auth/login` has no throttling. Combined with predictable seed passwords, enables offline brute-force or credential stuffing. |
| **No per-user device authorization** | `app.py`, lines 68, 98, 133 | All device endpoints use `get_current_user()` for authentication only. There is no `user_id` check against the device's owner — any authenticated user can access any device by ID. |
| **In-memory database** | `app.py`, line 16 | `sqlite3.connect(':memory:')` means all state is lost on restart. While not a vulnerability per se, it means audit logs, session revocations, and update history are ephemeral. |
| **No TLS / HTTPS enforcement** | `Dockerfile`, `app.py`, line 146 | `uvicorn.run(app, host='0.0.0.0', port=8097)` — no `ssl_certfile`/`ssl_keyfile`. Cookies are HttpOnly but not marked `secure`, so session tokens can be sent over plaintext connections. |

---

## 7. Unknowns & Areas Not Reviewed

| Area | Reason |
|---|---|
| **Runtime CORS / CSP configuration** | No CORS middleware or CSP headers observed in source, but a reverse proxy could inject them. |
| **Dockerfile hardening** | Running as root (default for `python:3.10-slim`), no `--user` flag, no non-root capability drop. |
| **Dependency supply-chain** | `requirements.txt` pins versions but does not include transitive dependency audits or SBOM. |
| **Exact firmware delivery mechanism** | The source fetches a binary but the code comment says "Simulates updating" — the actual push mechanism to hardware is opaque. |
| **Session store concurrency** | The `sessions` dict is shared global state without locks; potential race conditions on login/logout under load. |
| **DNS rebinding / SSRF circumvention** | Not evaluated; the SSRF is blind — an attacker would need to enumerate internal services manually. |

---

## 8. Remediation Priorities

| Priority | Action | Chain Broken |
|---|---|---|
| **P0 (Critical)** | Remove or authenticate `/api/debug/devices`; remove from production entirely | Chain #1 |
| **P0 (Critical)** | Whitelist allowed URLs and block private RFC1918 ranges in both SSRF endpoints | Chain #2, Chain #3 |
| **P1 (High)** | Add firmware signature / hash verification | Chain #3 |
| **P1 (High)** | Move seed passwords to environment variables or a secrets store; add rate limiting to `/api/auth/login` | Cross-cutting |
| **P2 (Medium)** | Add per-user device authorization checks | Cross-cutting |
| **P2 (Medium)** | Enable TLS, mark cookies `Secure`, add a non-root Docker user | Cross-cutting |

---

## 9. Recommended Tests

The following tests should be added to the test suite:

1. **`test_debug_endpoint_requires_auth`** — Verify that `/api/debug/devices` returns 401 without a valid session cookie.
2. **`test_sensor_data_blocks_internal_urls`** — Verify that `GET /api/devices/sensor-data?url=http://169.254.169.254/latest/meta-data/` returns 400 or 403.
3. **`test_sensor_data_blocks_private_ranges`** — Verify SSRF is blocked for `10.x`, `172.16-31.x`, `192.168.x`, and `127.x` URLs.
4. **`test_firmware_url_blocked_private`** — Same SSRF blocklist test for the firmware-update endpoint.
5. **`test_firmware_rejects_unsigned_payload`** — Verify the firmware endpoint rejects binaries without a valid signature.
6. **`test_login_rate_limited`** — Verify that repeated login attempts beyond a threshold return 429.
7. **`test_device_authz_scoped_to_owner`** — Verify that user B cannot access device_id=1 if device 1 is owned by user A.

---

*Report written statically from source code only. No live endpoints were probed.*
