

# ✅ Chained Vulnerability Audit Complete

The report has been written to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`.

## Audit Summary

### 4 Chained Vulnerabilities Detected

| # | Chain | Severity | Confidence |
|---|-------|----------|------------|
| 1 | **SSRF + Debug Endpoint → Internal Network Recon** | **HIGH** | HIGH |
| 2 | **Stored XSS via Messages → Agent Session Hijack** | **HIGH** | HIGH |
| 3 | **Debug Mode + SSRF → RCE + Full Internal Access** | **CRITICAL** | HIGH |
| 4 | **Hardcoded Credentials → Full Account Takeover** | **MEDIUM** | HIGH |

### Key Findings

- **`app.py` line 63**: `debug=True` with `host='0.0.0.0'` — the single most dangerous setting, enabling Werkzeug debugger RCE.
- **`app.py` line 9**: `requests.get(target_url)` — user-controlled URL passed to `requests` with no IP/protocol whitelist (SSRF).
- **`app.py` line 26**: `GET /api/debug/env` — dumps all environment variables with no auth, revealing DB connection strings and service URLs.
- **`static/index.html`**: Plaintext credentials (`alice`/`alice123`, `bob`/`bob123`, `agent_smith`/`agent123`) displayed in the HTML.
- **`static/js/app.js`**: 12 instances of `innerHTML` with dynamic user data, enabling stored XSS via the messages endpoint.

### Easiest Remediation Wins

1. Change `debug=True` → `debug=False` (1 character, breaks RCE chain)
2. Remove or auth-guard `/api/debug/env` (breaks information disclosure)
3. Add IP blocking + URL allowlisting to the SSRF handler (breaks SSRF chain)
4. Replace `innerHTML` with `textContent` in `app.js` (breaks XSS chain)
5. Remove hardcoded credentials from HTML (breaks account takeover chain)

### Areas Not Fully Reviewed

- Authentication handler implementation (`/api/auth/login`) was not in the visible `app.py` scope
- `/api/properties/analyze` subprocess handler referenced by frontend but not in visible source
- No `requirements.lock` / lockfile for supply-chain visibility
- No TLS/HTTPS configuration visible
