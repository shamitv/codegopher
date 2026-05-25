

The chained vulnerability static audit is complete. Here's a summary of what was found:

## Audit Results: 4 Chained Vulnerabilities Identified

### Chain #1 — Username Enumeration → MD5 Cracking → IDOR → PHI Exfiltration (HIGH)
- The login endpoint returns different error messages for "account not found" vs "wrong password", enabling username enumeration
- No brute-force lockout or rate limiting exists
- Passwords are hashed with unsalted MD5 (trivially crackable)
- The `/api/patients/<id>/records` endpoint has **no ownership check** — any authenticated user can fetch any patient's records by guessing the ID
- **Result**: Complete PHI exfiltration (diagnoses, prescriptions, blood type, DOB) for any patient

### Chain #2 — Hardcoded Credentials in Static HTML (HIGH)
- The `index.html` file contains a visible block with usernames and passwords for all seeded accounts (`alice/alice123`, `bob/bob123`, `dr_cyber/staff123`)
- **Result**: Zero-effort account takeover — anyone viewing the page can log in as any account

### Chain #3 — Hardcoded Secret Key + DEBUG=True → Session Forgery (HIGH)
- `SECRET_KEY` is hardcoded in `settings.py` and committed to source
- `DEBUG=True` and `ALLOWED_HOSTS=['*']` expose verbose errors and allow host-header attacks
- All views trust `request.session` values without database verification
- **Result**: Forged session cookies grant arbitrary user impersonation and admin access

### Chain #4 — Stored XSS via Appointments (MEDIUM)
- `create_appointment` accepts unsanitized input into `reason_for_visit`
- `app.js` renders appointment data via `innerHTML`, enabling XSS
- Staff/admin users viewing the appointments list would execute the payload
- **Result**: JavaScript execution in privileged user context

The full report has been written to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md` with detailed code references, Mermaid attack graphs, remediation priorities, and recommended tests.
