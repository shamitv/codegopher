

I've completed the chained vulnerability static audit of the Patient Portal codebase and written the report to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`.

## Summary of Findings

| Metric | Value |
|--------|-------|
| **Chains detected** | 4 |
| **Highest severity** | HIGH |
| **Confidence** | HIGH across all chains |

### Chains Identified

1. **Full PHI Exfiltration via IDOR** — Any authenticated patient can access another patient's complete medical records (prescriptions, diagnostic notes, DOB, blood type) because `get_patient_records` validates session presence but never checks that the session user owns the requested `patient_id`. A search endpoint further aids IDOR by leaking patient IDs.

2. **Weak Password Hashing + No Brute-Force Protection** — Passwords are hashed with MD5 (cryptographically broken, rainbow-table-able). Combined with zero rate limiting, no lockout, and trivially guessable seed credentials (`alice123`, `admin123`), this allows full account takeover via offline cracking or unlimited online brute force.

3. **CSRF-Exempt Auth APIs + Insecure Cookies** — Three critical endpoints (`login`, `logout`, `create_appointment`) are decorated with `@csrf_exempt` while session cookies have `SECURE=False` and `SAMESITE=Lax`. An attacker can forge requests to hijack sessions, log users in as themselves, or create fake appointments.

4. **Hardcoded Admin Credentials + DEBUG=True** — Django admin is exposed with a seeded admin account (`admin`/`admin123` via MD5), `DEBUG=True` leaks stack traces, and `ALLOWED_HOSTS=['*']` accepts any host. This grants full database control and potential RCE.

### Key Remediations (P0)
- Add ownership/role checks in `get_patient_records`
- Replace MD5 with PBKDF2/Argon2
- Set `DEBUG = False` and restrict `ALLOWED_HOSTS`
- Remove `@csrf_exempt` from API views
- Set `SESSION_COOKIE_SECURE = True` and `SAMESITE = 'Strict'`
