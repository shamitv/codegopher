

The chained vulnerability static audit is complete. Here's a summary of findings:

## Audit Results

**3 chained vulnerabilities** were identified in the IoT Device Dashboard:

1. **HIGH** — Stack trace + internal secret leak via device command error path → attacker obtains telemetry secret → accesses internal telemetry endpoint to steal all device keys
2. **HIGH** — SSRF via device status refresh (`axios.get` with user-supplied URL) → arbitrary internal service access, cloud credential theft via metadata endpoints
3. **MEDIUM** — No role-based access control on device commands → any authenticated user (even CUSTOMER role) can control any IoT device
4. **MEDIUM** — Weak session tokens (`Math.random()` instead of CSPRNG) + no session expiration/logout → session token prediction and persistence

### Key Cross-Cutting Weaknesses

- CORS misconfiguration (`origin: true` with credentials)
- Hardcoded debug credentials and seed passwords in source
- No rate limiting on auth endpoints
- Verbose error stack traces exposed to clients
- In-memory session store without persistence or rotation

### Recommendations

The **highest priority** fix is removing `gateway_config` and `stack` from the error response in the `/api/devices/command` catch handler — this single change breaks the highest-severity chain.

The full report has been written to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`.
