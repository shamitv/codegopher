

The report has been written to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`. Here's a summary of the audit:

## Audit Complete

**3 chained vulnerabilities** were identified, all rated **High** severity:

1. **Full Account Takeover** — Hardcoded `SECRET_KEY` (`settings.py:4`) + `@csrf_exempt` on all write endpoints (`views.py:23,44,68,93`) allow forging valid session cookies and bypassing CSRF, enabling impersonation of any user including staff.

2. **IDOR + Unauthorized Data Modification** — `permit_detail()` and `upload_document()` (`views.py:53-101`) use `Permit.objects.get(id=permit_id)` with no ownership or authorization checks. Any authenticated user can read and upload documents to any permit.

3. **Stored XSS / Arbitrary Code Serving** — Unrestricted file upload (`views.py:84-92`) accepts any file type without validation, and `DEBUG=True` with Django's `static()` media helper (`urls.py:14`) serves uploaded files publicly, creating a stored XSS vector.

**9 cross-cutting weaknesses** were also catalogued, including empty password validators, wildcard `ALLOWED_HOSTS`, in-memory SQLite, no rate limiting, and missing secure cookie flags.

**Recommended priority actions:**
- Rotate the hardcoded `SECRET_KEY`
- Remove all `@csrf_exempt` decorators
- Set `DEBUG=False` and validate file uploads
- Add ownership checks in `permit_detail` and `upload_document`
