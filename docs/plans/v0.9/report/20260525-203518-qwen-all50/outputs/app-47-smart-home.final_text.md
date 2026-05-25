

The chained vulnerability audit is complete. Here's a summary of what was found:

## Audit Results

**5 chained vulnerability paths detected**, with 3 at **High confidence** and 2 at **Medium confidence**:

| # | Chain | Severity | Confidence | Key Fix |
|---|---|---|---|---|
| 1 | Unauthenticated debug endpoint leaks all device API tokens → command injection | **High** | High | Add auth to `/api/debug/devices` |
| 2 | SSRF on sensor-data endpoint → internal network reconnaissance/data exfiltration | **High** | High | URL allowlist + IP blocking |
| 3 | Insecure firmware update (no signature/checksum verification) → supply chain compromise | **High** | Medium | Cryptographic signature verification |
| 4 | No role enforcement anywhere → any user has admin-equivalent capabilities | **High** | High | Implement `require_role()` dependency |
| 5 | Multi-vector: token leak + SSRF + firmware update = full IoT takeover | **High** | Medium | All of the above |

### Cross-Cutting Weaknesses (not forming complete chains)
- **Hardcoded credentials** in source (`alice_home_2026`, `admin_home_2026`)
- **Verbose error messages** exposing internal state via `detail=str(e)`
- **Weak rate limiting** (non-atomic, memory-only, single-value per user)
- **In-memory SQLite** with `check_same_thread=False`

The full report has been written to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md` with detailed Mermaid attack graphs, line references, and prioritized remediation steps.
