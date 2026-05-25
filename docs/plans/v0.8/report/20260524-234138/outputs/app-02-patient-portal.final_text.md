

The chained vulnerability static audit is complete. The report has been written to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`.

## Audit Summary

**2 High-severity chains detected** across this patient portal codebase:

### Chain 1: Credential Harvesting → MD5 Brute Force → Data Exfiltration (High)
- **Entry point:** Plaintext passwords hardcoded in `index.html` (lines 38-43) — `alice/alice123`, `bob/bob123`, `dr_cyber/staff123`
- **Weaknesses:** MD5 password hashing (`portal/models.py`), different error messages enabling username enumeration (`portal/views.py`), weak session cookie config (`SESSION_COOKIE_SECURE = False`)
- **Sink:** Unauthenticated-then-authenticated access to any patient's PHI via the records endpoint
- **Remediation:** Remove seed credentials, upgrade to PBKDF2/Argon2, enforce ownership checks

### Chain 2: IDOR → Bulk Patient Data Theft (High)
- **Entry point:** `GET /api/patients/<int:patient_id>/records` accepts any integer ID
- **Weakness:** No ownership authorization — only checks for valid session, compares nothing to the `patient_id` parameter. Frontend even provides a "Switch Record Vault" input for this purpose.
- **Sink:** Full patient data exposure (name, DOB, blood type, prescriptions, diagnostic notes) for any ID
- **Remediation:** Add `request.session['patient_id'] == patient_id` check, remove frontend IDOR control

### 8 Cross-Cutting Weaknesses
- Hardcoded `SECRET_KEY`
- `DEBUG = True`
- `ALLOWED_HOSTS = ['*']`
- Empty `AUTH_PASSWORD_VALIDATORS`
- `@csrf_exempt` on state-changing endpoints
- No rate limiting (explicitly commented in code)
- SQLite for production
- Potential stored XSS via `innerHTML` rendering

**Priority:** All P0 items (credentials removal, MD5 upgrade, ownership authorization, IDOR fix) must be remediated before the application handles any real user data.
