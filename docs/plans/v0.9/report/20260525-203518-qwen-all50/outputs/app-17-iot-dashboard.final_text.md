

The Chained Vulnerability Static Audit is complete. Here's a summary of findings:

## Audit Results

**4 chained vulnerabilities** were identified across the IoT Device Dashboard codebase:

| Chain | Severity | Description |
|-------|----------|-------------|
| **Chain 1** | HIGH | SSRF via `/api/devices/refresh` → Telemetry endpoint → Device secret exfiltration. User-supplied `statusUrl` is passed directly to `axios.get()` with no validation, and the internal telemetry endpoint has no IP restriction. |
| **Chain 2** | HIGH | Error information disclosure on `/api/devices/command` leaks the internal telemetry API key in the 500 response body. Combined with the unprotected telemetry endpoint, this enables full device key exfiltration. |
| **Chain 3** | MEDIUM–HIGH | Weak `Math.random()`-based session tokens + overly permissive CORS (`origin: true, credentials: true`) + zero CSRF protection → session hijacking and account takeover. |
| **Chain 4** | MEDIUM | `requireAuth` checks session existence but never validates roles. Any authenticated user (including `CUSTOMER` accounts) can send commands to any device with no ownership check. |

**10 additional cross-cutting weaknesses** were catalogued, including hardcoded credentials in seed data, hardcoded device secrets, no rate limiting, no HTTPS enforcement, and a never-used security guard helper (`allowedCallback`).

The full report with Mermaid attack graphs, line-referenced evidence, and prioritized remediation steps has been written to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`.
