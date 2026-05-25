

The chained vulnerability static audit is complete. Here's a summary of what was found:

### Audit Results

**3 chained vulnerability paths identified** across the Smart Home Device Manager codebase:

1. **CRITICAL — Unauthenticated Device Token Theft → Physical Device Control** (Chain #1)
   - `/api/debug/devices` returns all device API tokens with zero authentication
   - An unauthenticated attacker can then issue commands to any device (locks, garage doors, thermostats)

2. **CRITICAL — Authenticated SSRF → Internal Network Data Exfiltration** (Chain #2)
   - `/api/devices/sensor-data` passes a user-supplied URL directly to `requests.get()` with no validation
   - Any authenticated user can read data from internal services, cloud metadata endpoints, etc.

3. **HIGH — Authenticated SSRF + No Integrity Verification → Persistent Device Compromise** (Chain #3)
   - `/api/devices/{id}/firmware/update` also accepts arbitrary URLs (SSRF) and applies the fetched binary without signature or hash verification
   - Enables delivery of malicious firmware to any device in the inventory

### Cross-Cutting Weaknesses
- Hardcoded seeded passwords in source code
- No rate limiting on login endpoint
- No per-user device authorization (any user can access any device)
- In-memory database with no audit trail
- No TLS enforcement; cookies not marked `Secure`

### Recommendation Priority
- **P0**: Remove/authenticate the debug endpoint + whitelist URLs for both SSRF vectors
- **P1**: Add firmware signature verification and rate limiting on login
- **P2**: Add per-user device authorization and enable TLS/non-root Docker user

The full report has been written to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`.
