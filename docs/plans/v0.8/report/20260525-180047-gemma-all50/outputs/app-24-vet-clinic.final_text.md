

The chained vulnerability static audit is complete. The report has been written to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`.

## Audit Summary

### Chains Identified: 3

| Chain | Severity | Confidence | Description |
|---|---|---|---|
| **Chain 1** | HIGH | HIGH | Hardcoded JWT secret → SQL injection in pet search → Full database exfiltration |
| **Chain 2** | HIGH | HIGH | Hardcoded JWT secret → Admin forge → Zero-audit prescription tampering |
| **Chain 3** | MEDIUM | MEDIUM | Hardcoded JWT secret → Unauthorized pet owner assignment → Data integrity violation |

### Root Cause

A single root cause — the **hardcoded JWT secret** (`"secret123"` on line 14 of `app.py`) — enables **all three chains**. An attacker can forge tokens with any role offline, bypassing all role-based authorization checks.

### Easiest Fix (Breaks All 3 Chains)

```python
JWT_SECRET = os.environ.get("JWT_SECRET", "CHANGE-ME-TO-STRONG-RANDOM-KEY")
```

### Additional Critical Fix

The SQL injection in `/api/pets/search` (line 128) is independently severe and should be parameterized even if the JWT issue is fixed:

```python
cursor.execute("SELECT * FROM pets WHERE name LIKE ?", (f"%{q}%",))
```

### Cross-Cutting Weaknesses

No CSRF protection, no rate limiting on login, verbose error exposure, missing audit logging on prescription updates, no input length limits, and the container runs as root — all contributing to a weaker-than-required security posture.
