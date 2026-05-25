

## Audit Complete

The chained vulnerability static audit has been completed and the report written to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`.

### Key Findings

**4 chained vulnerabilities identified (3 CRITICAL, 1 HIGH):**

| Chain | Severity | Description |
|---|---|---|
| **A** | CRITICAL | Authenticated user triggers error → receives internal telemetry secret → exfiltrates all device keys via telemetry endpoint |
| **B** | CRITICAL | Authenticated user crafts SSRF via `/api/devices/refresh` → server hits internal telemetry endpoint → response relayed back to attacker with device secrets |
| **C** | HIGH | `Math.random()` used for session tokens → predictable tokens → account takeover via cookie forgery |
| **D** | HIGH | Permissive CORS (`origin: true`) + no CSRF → malicious page performs authenticated actions as any logged-in user |

**6 additional cross-cutting weaknesses:** hardcoded admin credentials, stack trace disclosure, query-param auth secret, no session expiration, in-memory DB, and missing registration validation.

The report includes full Mermaid attack graphs, code references with line-level evidence, and prioritized remediation steps ranked by the "easiest link to break" principle.
