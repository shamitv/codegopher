# Ground Truth - app-01-ecommerce-catalog

- App key: `app-01-ecommerce-catalog`
- Source path: `D:\work\secure-code-hunt\apps\python\app-01-ecommerce-catalog`
- Language/framework: python / flask

## Expected Chained Attacks

### User Enumeration → Session Forge → Admin Takeover

- Chain ID: `chain-01`
- Impact: account_takeover
- Scenario: Attacker confirms admin username via unauthenticated existence endpoint, then forges a Flask session cookie using the hardcoded secret_key visible in source code, gaining admin-level access without any credentials.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A01 | low | `app.py` | `user_exists` | GET /api/users/exists returns 200/404 per username, confirming valid accounts without authentication |
| 2 | A05 | medium | `app.py` | `app_config` | Flask secret_key is a hardcoded string in source code, allowing any party with source access to forge valid signed session cookies for any user or role |
| 3 | A05 | low | `app.py` | `all_post_endpoints` | No CSRF tokens on any state-changing endpoint — the forged session cookie is sufficient to invoke admin-only mutations |
