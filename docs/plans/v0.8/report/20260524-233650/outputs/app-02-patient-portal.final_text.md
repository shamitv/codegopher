

The chained vulnerability static audit is complete. I've written the full report to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`.

Here's a summary of what was found:

### Chains Detected: 3

| # | Severity | Chain |
|---|---|---|
| 1 | **CRITICAL** | Account enumeration (distinct login errors) + weak MD5 password hashing (no salt) → offline cracking → full account takeover including ADMIN/STAFF |
| 2 | **CRITICAL** | IDOR on `/api/patients/<id>/records` (no session-to-resource binding) → any authenticated user can exfiltrate all patients' medical records, prescriptions, and diagnostic notes |
| 3 | **HIGH** | Hardcoded credentials in source code (`seed_database`) + credentials exposed in HTML (`index.html` PIN SEEDS block) + hardcoded `SECRET_KEY` → immediate unauthorized admin login |

### Chain Detected: 1 Medium

| # | Severity | Chain |
|---|---|---|
| 4 | **MEDIUM** | `@csrf_exempt` on write endpoints (`create_appointment`) + session-only auth → cross-site request smuggling to create unauthorized appointments |

### Key Root Causes
- **No server-side authorization** on the records endpoint (Chain 2)
- **MD5 hashing without salt** (Chain 1)
- **Credentials leaked in multiple places** — source, HTML, and settings (Chain 3)
- **Production-hardening misconfigured** — `DEBUG=True`, `ALLOWED_HOSTS=['*']`, no validators, root Docker container
