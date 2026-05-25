

The chained vulnerability static audit is complete. The report has been written to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`.

## Summary of Findings

**4 attack chains detected:**

1. **SQL Injection → Donation Data Exfiltration** (HIGH) — The `/api/donations/search` endpoint constructs SQL queries via unsafe string interpolation (`f"SELECT * FROM donations WHERE donor_name LIKE '%{q}%' ..."`), enabling full extraction of donor PII, financial amounts, and Stripe transaction IDs. The `debug_query` response field literally hands the attacker the query template.

2. **Hardcoded Admin Credentials → Full Admin Compromise** (HIGH) — Seed data contains known plaintext passwords (`admin_pass_789`, `jane_pass_456`, `john_pass_123`). Combined with the login endpoint, this allows any attacker with source access to log in as admin and process refunds, view all data, and access audit logs.

3. **Admin Access + No Audit Logging → Unmonetized Financial Fraud** (MEDIUM) — The refund endpoint updates the database and confirms the refund, but makes **zero** calls to `log_audit_event()`. Unlike donation creation, which is logged, refunds are completely untraceable — enabling undetectable financial loss.

4. **Debug Mode + Verbose Error Exposure → Exploitation Enabler** (MEDIUM) — `debug=True` with `host='0.0.0.0'` exposes Flask's debugger and verbose error messages. Combined with the `debug_query` response field, this drastically lowers the skill floor for chains 1 and 2.

**Key cross-cutting weaknesses:** hardcoded `app.secret_key`, hardcoded `STRIPE_KEY`, CSRF only on donation submission (not logout/refund), no rate limiting, and server bound to all interfaces.

All chains have P0/P1 remediation with low effort — primarily parameterized queries, removing hardcoded secrets, adding audit logging, and disabling debug mode.
