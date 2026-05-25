

The chained vulnerability audit report has been written to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`.

## Audit Summary

I analyzed all files in this Flask-based e-commerce catalog codebase and identified **4 chained vulnerabilities**:

### Chains Found

| # | Chain | Severity | Confidence |
|---|---|---|---|
| 1 | **SQL Injection via product search** → full database read | **CRITICAL** | High |
| 2 | **SQL Injection + plaintext passwords** → complete admin account takeover | **CRITICAL** | High |
| 3 | **IDOR in order details endpoint** → cross-user data exfiltration | **HIGH** | High |
| 4 | **Missing CSRF + session auth** → unauthorized order placement | **MEDIUM** | Medium |

### Bonus Chain
A **stored XSS chain** was also identified: SQL injection can store `<script>` payloads in product names, which are then rendered unsanitized via `innerHTML` in the frontend JavaScript.

### Key Findings
- **`app.py:171`** — SQL injection via f-string in product search (the most critical vulnerability)
- **`app.py:80-82`** — All user passwords stored in plaintext
- **`app.py:219`** — Order details endpoint has no ownership verification (IDOR)
- **`static/index.html:63-65`** — All account credentials are visible in the rendered HTML
- **`app.py:286`** — Debug mode enabled with `host='0.0.0.0'`
- **`app.py:8`** — Session secret key is hardcoded

### Top Remediations
1. Parameterize SQL queries
2. Implement password hashing
3. Add ownership checks on all data endpoints
4. Remove plaintext credentials from the frontend
5. Disable debug mode
