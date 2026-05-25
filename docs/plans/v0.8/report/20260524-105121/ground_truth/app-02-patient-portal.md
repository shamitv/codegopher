# Ground Truth - Healthcare Patient Portal

- App key: `app-02-patient-portal`
- Source path: `D:\work\secure-code-hunt\apps\python\app-02-patient-portal`
- Language/framework: python / django

## Expected Chained Attacks

### User Enumeration → Offline MD5 Crack → Medical Records Exfiltration

- Chain ID: `chain-01`
- Impact: db_exfiltration
- Scenario: Attacker enumerates valid patient usernames via distinct login error messages, cracks the unsalted MD5 password hash offline, authenticates, uses the patient search endpoint to collect all patient IDs, then dumps every patient's medical records via the IDOR endpoint.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A07 | low | `portal/views.py` | `login_view` | Login endpoint returns distinct error messages for unknown username vs wrong password, enabling username enumeration |
| 2 | A02 | high | `portal/models.py` | `set_password_md5` | Passwords stored as unsalted MD5 hashes, crackable offline via rainbow tables or GPU brute force |
| 3 | A01 | low | `portal/views.py` | `search_patients` | Patient search endpoint returns IDs for all patients regardless of the authenticated user's own identity, enabling mass IDOR enumeration |
