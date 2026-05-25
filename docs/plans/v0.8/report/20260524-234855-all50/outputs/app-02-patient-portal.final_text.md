

## Chained Vulnerability Audit Complete

The audit of the Nexus Health Vault Patient Portal has been completed and the full report is written to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`.

### Key Findings

| Chain | Severity | Description |
|-------|----------|-------------|
| **Chain 1** | **HIGH** | IDOR on `/api/patients/<id>/records` — any authenticated user can read any patient's PHI by simply changing the ID parameter. The view checks authentication but never verifies ownership. |
| **Chain 2** | **CRITICAL** | MD5 password hashing + username enumeration → full credential compromise. The app returns different error messages for "account not found" vs "wrong password", allowing attacker to build a username list and then crack MD5 hashes offline in seconds. Plaintext credentials are even hardcoded in the HTML. |
| **Chain 3** | **HIGH** | Stored XSS via appointment `reason_for_visit` field + missing CSRF protection. The frontend uses `innerHTML` to render unescaped user input, and the endpoint is `@csrf_exempt`, enabling cross-user data theft and session manipulation. |

### Cross-Cutting Weaknesses
- Plaintext credential seeds in HTML
- `DEBUG = True` with `ALLOWED_HOSTS = ['*']`
- `SESSION_COOKIE_SECURE = False`
- No rate limiting on login
- Empty password validators
- Three endpoints are `@csrf_exempt`

### Top Priority Remediations
1. Replace MD5 with Django's PBKDF2/Argon2 hashing
2. Add ownership check in `get_patient_records()`
3. Remove `@csrf_exempt` from `create_appointment` and fix the `innerHTML` XSS
4. Remove plaintext credentials, disable DEBUG, restrict ALLOWED_HOSTS
